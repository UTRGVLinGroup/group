"""Double-click launcher; failures are shown instead of disappearing in a console."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
try:
    from editor import main
    main()
except Exception as exc:
    from tkinter import Tk, messagebox
    root=Tk(); root.withdraw()
    messagebox.showerror('Website editor could not open',str(exc)+'\n\nSee management/START-HERE.md for help.')
    root.destroy()
