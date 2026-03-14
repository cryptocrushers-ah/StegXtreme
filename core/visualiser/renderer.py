import base64
import io
import matplotlib.pyplot as plt

def render_fig_base64(fig: plt.Figure) -> str:
    """Renders a matplotlib figure to a base64 encoded PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
    buf.seek(0)
    b64_str = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{b64_str}"
