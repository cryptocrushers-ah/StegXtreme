import base64
from io import BytesIO
import matplotlib.pyplot as plt  # type: ignore

def render_fig_base64(fig: plt.Figure) -> str:
    """
    Saves a matplotlib figure to a BytesIO buffer and returns the base64 encoded
    PNG string. Closes the figure to free memory.
    """
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1)
    buf.seek(0)
    b64_str = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64_str
