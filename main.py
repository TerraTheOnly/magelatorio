import sys
import traceback


def enableHighDpi():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def reportStartupError(message):
    print(message, file=sys.stderr)
    try:
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        messagebox.showerror("Magelatório", message)
        root.destroy()
    except Exception:
        pass


def main():
    try:
        import tkinter
        from app.gui import ReportApp
    except ImportError as error:
        if getattr(error, "name", None) == "tkinter":
            reportStartupError("O tkinter não foi encontrado.\nNo Linux instale com: sudo apt install python3-tk")
        else:
            reportStartupError(f"Falta uma biblioteca: {error}\nInstale com: pip install -r requirements.txt")
        sys.exit(1)

    enableHighDpi()
    try:
        root = tkinter.Tk()
        ReportApp(root)
        root.mainloop()
    except Exception:
        reportStartupError("Erro inesperado:\n\n" + traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
