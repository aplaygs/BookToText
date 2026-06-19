#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import platform

def print_step(msg):
    print(f"\n\033[1;34m===> {msg}\033[0m")

def print_error(msg):
    print(f"\n\033[1;31m[ОШИБКА] {msg}\033[0m")

def print_success(msg):
    print(f"\n\033[1;32m[УСПЕХ] {msg}\033[0m")

def check_os():
    if platform.system() != 'Darwin':
        print_error("Скрипт деплоя предназначен только для macOS.")
        sys.exit(1)

def run_tests():
    print_step("Запуск автоматических тестов...")
    result = subprocess.run([sys.executable, "test_runner.py"])
    if result.returncode != 0:
        print_error("Тесты не пройдены. Сборка прервана в целях безопасности.")
        sys.exit(1)
    print_success("Все тесты пройдены успешно!")

def check_app_running():
    print_step("Проверка запущенных экземпляров BookToText...")
    try:
        # Check if the process is running
        output = subprocess.check_output(["pgrep", "-f", "BookToText.app"], text=True)
        if output.strip():
            print_error("Приложение BookToText сейчас запущено. Пожалуйста, закройте его перед обновлением.")
            sys.exit(1)
    except subprocess.CalledProcessError:
        # pgrep returns non-zero if no processes matched. This is the expected/safe path.
        pass

def build_app():
    print_step("Сборка приложения с помощью PyInstaller...")
    # Using python -m PyInstaller to ensure it uses the active environment
    build_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", "BookToText",
        "--icon=icon.icns",
        "main.py"
    ]
    result = subprocess.run(build_cmd)
    if result.returncode != 0:
        print_error("Ошибка при сборке PyInstaller.")
        sys.exit(1)
    print_success("Сборка завершена успешно!")

def deploy_app():
    print_step("Обновление приложения в папке /Applications...")
    src_dir = os.path.join(os.getcwd(), "dist", "BookToText.app")
    dest_dir = "/Applications/BookToText.app"

    if not os.path.exists(src_dir):
        print_error(f"Собранное приложение не найдено по пути: {src_dir}")
        sys.exit(1)

    try:
        if os.path.exists(dest_dir):
            print("Удаление старой версии из /Applications...")
            shutil.rmtree(dest_dir)
        
        print("Копирование новой версии...")
        shutil.copytree(src_dir, dest_dir)
        print_success("Приложение успешно установлено в /Applications/BookToText.app")
    except Exception as e:
        print_error(f"Ошибка при копировании файлов: {e}")
        sys.exit(1)

def notify_user():
    print_step("Отправка системного уведомления...")
    script = 'display notification "Обновление завершено! Новая версия установлена в Программы." with title "BookToText Deploy"'
    subprocess.run(["osascript", "-e", script])

def main():
    print("\n" + "="*50)
    print("🚀 Автоматический сборщик и деплой BookToText")
    print("="*50)
    
    check_os()
    run_tests()
    check_app_running()
    build_app()
    deploy_app()
    notify_user()
    
    print("\n" + "="*50)
    print("✨ Деплой полностью завершен. Приложение можно запускать!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
