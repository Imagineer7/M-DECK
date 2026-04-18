# ui/components.py
import flet as ft

def show_snackbar(page, message, success=True):
    async def _update_snackbar():
        page.snack_bar = ft.SnackBar(
            ft.Text(message, color=ft.Colors.WHITE),
            bgcolor="#4caf50" if success else "#f44336",
            open=True,
            duration=3000
        )
        page.update()

    try:
        page.run_task(_update_snackbar)
    except RuntimeError:
        print(message)