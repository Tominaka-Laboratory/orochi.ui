import gradio as gr
from .markdown import general
from .utils.param_box import param_boxes
from .listeners.module import run_module

def add_panel(self, 
                  module, # Analyzer instance
                  keys: list, 
                  title="AI Analysis", 
                  header=None, 
                  footer=None):
        """
        Autonomous AI analysis panel.
        Uses a periodic timer to update optimization progress (Rw trajectory and reasoning log) in real time.
        """
        self.ana_step_id = -1
        self.replot = gr.State(False)


        with gr.Column(visible=False) as new_panel:
            if header: gr.Markdown(header)

            # Start and stop buttons
            with gr.Row():
                run_btn = gr.Button("🚀 Start Cycle", variant="primary")
                stop_btn = gr.Button("⏹ Stop", variant="secondary")

            # --- 1. Monitoring section ---
            with gr.Tab("Visualize"):

                gr.Markdown("## 🗺 AI Reasoning Lineage Map")
                lineage_map = gr.Plot() 
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🧠 Current Reasoning")
                        ai_thought = gr.Textbox(lines=8, interactive=False)
                    with gr.Column(scale=1):
                        gr.Markdown("### 📈 Rw Convergence")
                        progress_plot = gr.Plot()

                timer = gr.Timer(value=2.0, active=False)
                
                # Event listeners
                run_btn.click(fn=lambda: gr.update(active=True), outputs=timer).then(fn=run_module(module))
                stop_btn.click(fn=lambda: setattr(module, "_state", "STOP"))

                timer.tick(
                            fn=check_if_updated(self, module),
                            outputs=[self.replot]
                           ).then(
                            fn=refresh_ai_monitor(self, module),
                            inputs=[self.replot],
                            outputs=[lineage_map, progress_plot, ai_thought])


            # --- 2. Parameters section ---
            with gr.Tab("Parameters"):
                gr.Markdown("## Parameters")
                with gr.Row():
                    triggers = [self.ui.load]
                    non_dic_keys = set(keys) - set(["allowed_actions", "system_prompts", "user_prompts"])
                    param_boxes(module, list(non_dic_keys), triggers=triggers)

                dic_keys = set(keys) & set(["allowed_actions", "system_prompts", "user_prompts"])
                for key in dic_keys:
                    with gr.Column():
                        triggers = [self.ui.load]
                        param_boxes(module, [key], triggers=triggers)
                

                if footer: gr.Markdown(footer)
                self._panels[title] = new_panel


def check_if_updated(self, module):
    def action():
        sid = module.step_id
        if sid != self.ana_step_id:
            self.ana_step_id = sid
            return True
        return False
    return action

def refresh_ai_monitor(self, module):
    """
    Called on timer tick to refresh the analysis lineage map and Rw convergence plot.
    """
    import plotly.graph_objects as go
    import networkx as nx

    def action(update_flag):
        if not update_flag:
            return gr.update(), gr.update(), gr.update()

        data = module.memory.to_mindmap_data()
        if not data["nodes"]:
            return gr.update(), gr.update(), "No data available."

        # --- 1. Build lineage graph (tree layout) ---
        G = nx.DiGraph()
        for n in data["nodes"]:
            G.add_node(n["id"], **n)
        for e in data["edges"]:
            G.add_edge(e["source"], e["target"])

        # Compute hierarchical layout
        pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='dot') if hasattr(nx, 'nx_agraph') else nx.spring_layout(G)
        
        # Render edges and nodes with Plotly
        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        node_x, node_y, node_color, node_text = [], [], [], []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_color.append(G.nodes[node]['score'])
            node_text.append(G.nodes[node]['label'])

        fig_map = go.Figure(data=[
            go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='#888'), hoverinfo='none'),
            go.Scatter(x=node_x, y=node_y, mode='markers+text', text=node_text, textposition="bottom center",
                        marker=dict(size=25, color=node_color, colorscale='RdYlGn', reversescale=True, 
                                    showscale=True, colorbar=dict(title="Rw")))
        ])
        fig_map.update_layout(title="AI Research Lineage (Mind Map)", showlegend=False,
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))

        # --- 2. Rw trajectory ---

        fig_score = go.Figure(data=[
            go.Scatter(x=data["nodes"]["id"], y=data["nodes"]["gof_score"], mode='lines+markers')
        ])
        fig_score.update_layout(title="Goodness of Fit", showlegend=False,
                                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))

        # --- 3. Retrieve latest reasoning log ---
        latest_thought = module.memory.get_step_data(-1)[0]["thought_process"]

        return fig_map, fig_score, latest_thought



    return action