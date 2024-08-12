from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from PIL import Image
import io
import os
import time
import datetime

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta según tu configuración
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class URLRequest(BaseModel):
    url: str
    div_id: str


chromedriver_path = os.path.join(
    os.path.dirname(__file__), "chromedriver-win64", "chromedriver.exe"
)


@app.post("/screenshot/")
async def capture_screenshot(request: URLRequest):
    url = request.url
    div_id = request.div_id
    driver = None
    try:
        # Configurar Selenium
        options = Options()
        options.add_argument("--disable-gpu")  # Desactivar GPU
        options.add_argument("--force-device-scale-factor=1")
        options.add_argument("--headless")  # Opcional: Ejecutar en modo sin cabeza
        service = Service(chromedriver_path)  # Ruta a chromedriver
        driver = webdriver.Chrome(service=service, options=options)

        # Configurar tamaño de ventana
        driver.set_window_size(1920, 1080)

        # Cargar la página
        driver.get(url)

        # Esperar a que el div con el id específico esté presente y visible
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.ID, div_id)))

        # Añadir un pequeño retraso para asegurarse de que todo esté cargado
        time.sleep(30)

        # Encontrar el div específico
        div_element = driver.find_element(By.ID, div_id)

        # Obtener las dimensiones del div
        location = div_element.location_once_scrolled_into_view
        size = div_element.size

        # Capturar screenshot de toda la página
        screenshot = driver.get_screenshot_as_png()

        # Convertir a imagen
        image = Image.open(io.BytesIO(screenshot))

        # Cortar la imagen para enfocarse solo en el div
        left = location["x"]
        top = location["y"]
        right = left + size["width"]
        bottom = top + size["height"]
        image = image.crop((left, top, right, bottom))

        # Obtener la ruta de la carpeta "Downloads"
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")

        # Generar un nombre de archivo único basado en la fecha y hora actual
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = f"screenshot_{timestamp}.png"
        image_path = os.path.join(downloads_folder, image_filename)

        # Guardar la imagen en la carpeta "Downloads"
        image.save(image_path)

        driver.quit()  # Cerrar el driver

        return {"path": image_path}
    except Exception as e:
        if driver:
            driver.quit()  # Cerrar el driver en caso de error
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
