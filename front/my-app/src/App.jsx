import { useState } from 'react';
import './App.css'

function App() {
  const [process, setProcess] = useState("compress"); 
  const [samplingStep, setSamplingStep] = useState("0.01"); 
  const [matrixRank, setMatrixRank] = useState("3");     
  const [bitPerQuant, setBitPerQuant] = useState("8");  
  const [imageFile, setImageFile] = useState(null);
  const [downloadUrl, setDownloadUrl] = useState(null); // ссылка для скачивания
  const [downloadName, setDownloadName] = useState(null);

  // Обработка выбора файла
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setImageFile(file);
    }
  };

  // Отправка файла на сервер и получение результата
  const handleExecute = async () => {
  if (!imageFile) {
    alert("Пожалуйста, загрузите изображение!");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("file", imageFile);

    let urlEndpoint = "";
    let downloadFileName = "";

    if (process === "compress") {
      urlEndpoint = `http://localhost:8000/api/img/compress?h=${samplingStep}&rank=${matrixRank}&qbits=${bitPerQuant}`;
      downloadFileName = "compressed.exp";
    } else if (process === "decompress") {
      urlEndpoint = `http://localhost:8000/api/img/decompress?h=${samplingStep}&rank=${matrixRank}&qbits=${bitPerQuant}`;
      downloadFileName = "decompressed.jpg";
    } else {
      alert("Выберите корректный процесс!");
      return;
    }

    // POST-запрос
    const response = await fetch(urlEndpoint, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error("Ошибка при вызове API");
    }

    // Получаем файл как blob
    const blob = await response.blob();

    // Создаем временную ссылку для скачивания
    const url = window.URL.createObjectURL(blob);
    setDownloadUrl(url);
    setDownloadName(downloadFileName);

    alert("Файл успешно обработан и готов для скачивания!");
  } catch (error) {
    console.error(error);
    alert("Ошибка при отправке файла на сервер");
  }
};


  // Скачать файл
  const handleDownload = () => {
    if (!downloadUrl) return;
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = downloadName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    // Можно очистить URL после скачивания, если нужно
    // window.URL.revokeObjectURL(downloadUrl);
  };

  return (
    <>
      <div>
      <div className='center'>
        <h1 className='center'>Выберите процесс: </h1>
        <select
          value={process}
          onChange={(e) => setProcess(e.target.value)}
        >
          <option value="compress">Сжать изображения</option>
          <option value="decompress">Распаковать изображение</option>
        </select>
      </div>

        <h1 className='center'>Введите значения переменных: </h1>
        <div className="input-row">
          <div>
            <p className='center'>Шаг дискретизации</p>
            <input
              type="text"
              value={samplingStep}
              onChange={(e) => setSamplingStep(e.target.value)}
            />
          </div>

          <div>
            <p className="center">Ранг матрицы</p>
            <input
              type="text"
              value={matrixRank}
              onChange={(e) => setMatrixRank(e.target.value)}
            />
          </div>

          <div>
            <p className="center">Бит на квантование</p>
            <input
              type="text"
              value={bitPerQuant}
              onChange={(e) => setBitPerQuant(e.target.value)}
            />
          </div>
        </div>

        <h1 className='center'>Загрузите изображение: </h1>
        <div className='center'>
        <input type="file" accept="image/*" onChange={handleImageChange} />
      </div>
      </div>

      <div className="button-row">
        <button onClick={handleExecute}>Выполнить</button>
        {downloadUrl && (
          <button onClick={handleDownload}>Скачать файл</button>
        )}
      </div>
    </>
  );
}

export default App;
