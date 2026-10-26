"""JavaScript injector for interactive Fullscreen display of Plotly plots in Orochi UI.

Enables native full-screen expansion for all 2D and 1D Plotly graphs, automatically
resizing Plotly layouts to fill the user's entire monitor display for detailed inspection.
"""

FULLSCREEN_JS = """
<script>
(function() {
    function getPlotContainer(plotEl) {
        return plotEl.closest('.block') || plotEl.closest('.gradio-plot') || plotEl.parentElement;
    }

    function resizePlot(container, isFs) {
        const btn = container.querySelector('.orochi-fullscreen-btn');
        const plotEl = container.querySelector('.js-plotly-plot');
        if (btn) {
            const iconExpand = btn.querySelector('.orochi-fs-icon-expand');
            const iconCompress = btn.querySelector('.orochi-fs-icon-compress');
            const label = btn.querySelector('.orochi-fs-label');
            if (isFs) {
                if (iconExpand) iconExpand.style.display = 'none';
                if (iconCompress) iconCompress.style.display = 'inline-block';
                if (label) label.textContent = 'Exit (Esc)';
                btn.classList.add('active');
            } else {
                if (iconExpand) iconExpand.style.display = 'inline-block';
                if (iconCompress) iconCompress.style.display = 'none';
                if (label) label.textContent = 'Fullscreen';
                btn.classList.remove('active');
            }
        }
        if (window.Plotly && plotEl) {
            if (isFs) {
                if (!plotEl._orochiOrigHeight) {
                    plotEl._orochiOrigHeight = (plotEl.layout && plotEl.layout.height) ? plotEl.layout.height : 650;
                }
                setTimeout(() => {
                    Plotly.relayout(plotEl, {
                        height: window.innerHeight - 45,
                        autosize: true
                    }).then(() => {
                        Plotly.Plots.resize(plotEl);
                    });
                }, 50);
            } else {
                setTimeout(() => {
                    const origH = plotEl._orochiOrigHeight || 650;
                    Plotly.relayout(plotEl, {
                        height: origH,
                        autosize: true
                    }).then(() => {
                        Plotly.Plots.resize(plotEl);
                    });
                }, 50);
            }
        }
    }

    function initPlotFullscreen() {
        const allPlotlyPlots = document.querySelectorAll('.js-plotly-plot');
        allPlotlyPlots.forEach(plotEl => {
            const container = getPlotContainer(plotEl);
            if (!container || container.querySelector('.orochi-fullscreen-btn')) return;

            container.style.position = 'relative';

            const btn = document.createElement('button');
            btn.className = 'orochi-fullscreen-btn';
            btn.type = 'button';
            btn.title = 'Toggle Fullscreen (全画面表示 / Escキーで解除)';
            btn.innerHTML = `
                <svg class="orochi-fs-icon-expand" viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"></path>
                </svg>
                <svg class="orochi-fs-icon-compress" style="display:none;" viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"></path>
                </svg>
                <span class="orochi-fs-label">Fullscreen</span>
            `;

            function toggleFs() {
                const isFs = container.classList.contains('orochi-fs-active') || document.fullscreenElement === container;
                if (!isFs) {
                    if (container.requestFullscreen) {
                        container.requestFullscreen().then(() => {
                            container.classList.add('orochi-fs-active');
                            resizePlot(container, true);
                        }).catch(() => {
                            container.classList.add('orochi-fs-active');
                            resizePlot(container, true);
                        });
                    } else {
                        container.classList.add('orochi-fs-active');
                        resizePlot(container, true);
                    }
                } else {
                    if (document.fullscreenElement) {
                        document.exitFullscreen().catch(() => {});
                    }
                    container.classList.remove('orochi-fs-active');
                    resizePlot(container, false);
                }
            }

            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleFs();
            });

            container.appendChild(btn);
        });
    }

    document.addEventListener('fullscreenchange', () => {
        const activeContainer = document.querySelector('.orochi-fs-active') || document.fullscreenElement;
        if (!document.fullscreenElement) {
            document.querySelectorAll('.orochi-fs-active').forEach(c => {
                c.classList.remove('orochi-fs-active');
                resizePlot(c, false);
            });
        } else if (activeContainer) {
            resizePlot(activeContainer, true);
        }
    });

    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.orochi-fs-active').forEach(c => {
                c.classList.remove('orochi-fs-active');
                if (document.fullscreenElement) {
                    document.exitFullscreen().catch(() => {});
                }
                resizePlot(c, false);
            });
        }
    });

    const observer = new MutationObserver(() => {
        initPlotFullscreen();
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            initPlotFullscreen();
            observer.observe(document.body, { childList: true, subtree: true });
        });
    } else {
        initPlotFullscreen();
        observer.observe(document.body, { childList: true, subtree: true });
    }

    let count = 0;
    const interval = setInterval(() => {
        initPlotFullscreen();
        count++;
        if (count > 25) clearInterval(interval);
    }, 400);
})();
</script>
"""

