import subprocess

if __name__ == "__main__":
    print("Запускаем сборку фронтенда...")

    try:
        subprocess.run("npm run dev", shell=True, cwd="frontend", check=True)
    except KeyboardInterrupt:
        print("\nФронтенд успешно остановлен.")