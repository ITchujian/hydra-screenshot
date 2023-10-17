from Views import TrayProgram
import ctypes

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("starter")
if __name__ == '__main__':
    tray_program = TrayProgram()
    tray_program.run()
