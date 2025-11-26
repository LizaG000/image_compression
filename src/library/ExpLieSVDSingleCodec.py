from dahuffman import HuffmanCodec
import numpy as np
from scipy.linalg import expm
import os, struct, pickle, argparse
from PIL import Image
from numpy.typing import NDArray
from typing import Optional
from io import BytesIO


class ExpLieSVDSingleCodec:
    _file_size_bytes: int | None = None
    rank: int = 3
    qbits: int = 6
    name: str = "name"
    _total_pixels: int | None = None
    _bpp: float | None = None
    _reconstructed_gray: Optional[NDArray[np.float16]] | None = None
    _compress_gray: Optional[NDArray[np.float16]] | None = None
    _original_gray: Optional[NDArray[np.float16]] | None = None
    blk = 4


    def __init__(self, h: float=0.2, rank: int=4, qbits: int=8, name:str="new"):
        self.h = h
        self.rank = rank
        self.qbits = qbits
        self.name = name


    def get_metric(self):
        return self._bpp, self._file_size_bytes

    def compress(self, img: BytesIO) -> bytes:
        img.seek(0)
        gray_im = Image.open(img).convert('L')
        self._original_gray = np.asarray(gray_im, dtype=np.float16)

        blocks, H, W = self._img_to_blocks(gray_im)

        quant_stream = b''

        # 1. Сначала собираем ВСЕ delta_low для вычисления глобального диапазона
        all_delta_lows = []
        for X in blocks:
            delta = expm(self.h * X) - np.eye(self.blk, dtype=np.float16)
            delta_low = self._low_rank_matrix(delta)
            all_delta_lows.append(delta_low)

        # 2. Находим глобальные min/max
        global_min = min(dl.min() for dl in all_delta_lows)
        global_max = max(dl.max() for dl in all_delta_lows)

        # 3. Новый метод квантования с глобальным диапазоном
        for delta_low in all_delta_lows:
            quant = self._quantize_with_global_range(delta_low, global_min, global_max)
            quant_stream += quant.tobytes()

        # Сжимаем ТОЛЬКО квантованные данные
        codec = HuffmanCodec.from_data(quant_stream)
        compressed_quant = codec.encode(quant_stream)

        # Сохраняем глобальные min/max в meta
        meta = (H, W, global_min, global_max, codec.get_code_table())
        meta_b = pickle.dumps(meta)

        # Собираем итоговый поток (range_stream УБРАН!)
        result = struct.pack('>H', len(meta_b)) + meta_b + compressed_quant
        _compress_gray = result

        self._file_size_bytes = len(result)
        self._total_pixels = H * W
        self._bpp = self._file_size_bytes * 8 / self._total_pixels
        return result

    def decompress(self, comp_bytes: BytesIO):
        comp_bytes_data = comp_bytes.getvalue()
        blocks, H, W = self._decompress_blocks(comp_bytes_data)
        rec = self._blocks_to_img(blocks, H, W)
        if rec.dtype == np.uint8:
            pil_image = Image.fromarray(rec)
        else:
            # Если данные не uint8, нормализуем
            rec_normalized = (rec - rec.min()) / (rec.max() - rec.min()) * 255
            pil_image = Image.fromarray(rec_normalized.astype(np.uint8))

        # Конвертируем в bytes
        img_byte_arr = BytesIO()
        pil_image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        self._reconstructed_gray = np.asarray(rec, dtype=np.float16)
        return img_bytes

    # ==================== метрики ====================
    def psnr(self,) -> float:
        img1 = self._original_gray
        img2 = self._reconstructed_gray
        print(img1 is None)
        print(img2 is None)
        h1, w1 = img1.shape
        h2, w2 = img2.shape

        # Обрезаем до минимального размера
        h_min = min(h1, h2)
        w_min = min(w1, w2)

        img1_cropped = img1[:h_min, :w_min]
        img2_cropped = img2[:h_min, :w_min]

        # Вычисляем PSNR для обрезанных изображений
        mse = np.mean((img1_cropped.astype(float) - img2_cropped.astype(float)) ** 2)

        if mse == 0:
            return float('inf')

        return 20 * np.log10(255.0 / np.sqrt(mse))

    @staticmethod
    def _save_side_by_side(orig: np.ndarray, rec: np.ndarray, out_path: str):
        h_orig, w_orig = orig.shape
        h_rec, w_rec = rec.shape

        # Определяем максимальные размеры
        max_h = max(h_orig, h_rec)
        max_w = max(w_orig, w_rec)

        # Создаем холст для двух изображений рядом
        side = np.zeros((max_h, 2 * max_w), dtype=np.uint8)

        # Размещаем оригинальное изображение (слева)
        side[:h_orig, :w_orig] = orig.astype(np.uint8)

        # Размещаем восстановленное изображение (справа)
        side[:h_rec, max_w:max_w + w_rec] = rec.astype(np.uint8)

        Image.fromarray(side).save(out_path)

    # ==================== внутренние методы ====================
    def _img_to_blocks(self, gray_im):
        gray = np.asarray(gray_im, dtype=np.float16)
        H, W = gray.shape
        H, W = (H // self.blk) * self.blk, (W // self.blk) * self.blk
        gray = gray[:H, :W]
        blocks = []
        for i in range(0, H, self.blk):
            for j in range(0, W, self.blk):
                blocks.append(gray[i:i + self.blk, j:j + self.blk] / 255.0)
        return blocks, H, W

    def _low_rank_matrix(self, delta: np.ndarray) -> np.ndarray:
        U, s, Vt = np.linalg.svd(delta, full_matrices=False)
        return U[:, :self.rank] @ np.diag(s[:self.rank]) @ Vt[:self.rank, :]

    def _quantize_with_global_range(self, mat: np.ndarray, global_min: float, global_max: float):
        """Квантование с использованием глобального диапазона"""
        if global_max == global_min:
            return np.zeros_like(mat, dtype=np.uint8)
        scale = (1 << self.qbits) - 1
        q = np.round((mat - global_min) / (global_max - global_min) * scale).astype(np.uint8)
        return q

    def _blocks_to_img(self, blocks, H, W):
        """
        Собирает блоки обратно в изображение
        """
        # Создаем пустое изображение
        reconstructed = np.zeros((H, W), dtype=np.float16)

        # Индекс текущего блока
        block_idx = 0

        # Заполняем изображение блоками
        for i in range(0, H, self.blk):
            for j in range(0, W, self.blk):
                if block_idx < len(blocks):
                    # Помещаем блок на свое место
                    reconstructed[i:i + self.blk, j:j + self.blk] = blocks[block_idx]
                    block_idx += 1

        # Конвертируем в uint8 для сохранения
        reconstructed = np.clip(reconstructed * 255, 0, 255).astype(np.uint8)
        return reconstructed

    def _decompress_blocks(self, byte_data):
        # Читаем meta
        meta_len = struct.unpack('>H', byte_data[:2])[0]
        meta_pickled = byte_data[2:2 + meta_len]

        # Новый формат meta: (H, W, global_min, global_max, code_table)
        H, W, global_min, global_max, table = pickle.loads(meta_pickled)

        # Оставшиеся данные после meta - ТОЛЬКО compressed_quant
        compressed_quant = byte_data[2 + meta_len:]

        # Декодируем Хаффманом
        codec = HuffmanCodec(table)
        quant_stream = bytes(codec.decode(compressed_quant))

        # Проверяем размер quant_stream
        n_blocks = (H // self.blk) * (W // self.blk)
        expected_quant_size = n_blocks * self.blk * self.blk

        if len(quant_stream) == 0:
            raise ValueError("quant_stream пустой после декодирования Хаффмана!")

        if len(quant_stream) != expected_quant_size:
            print(f"WARNING: quant_stream размер {len(quant_stream)}, ожидался {expected_quant_size}")

        blocks = []
        quant_off = 0

        for i in range(n_blocks):
            # Читаем квантованные данные
            quant = np.frombuffer(
                quant_stream[quant_off:quant_off + self.blk * self.blk],
                dtype=np.uint8
            ).reshape((self.blk, self.blk))
            quant_off += self.blk * self.blk

            # Используем глобальный диапазон вместо индивидуального
            delta_low = self._dequantize_with_global_range(quant, global_min, global_max)
            blocks.append(np.clip(delta_low / self.h, 0, 1))

        return blocks, H, W

    def _dequantize_with_global_range(self, quant: np.ndarray, global_min: float, global_max: float):
        """Деквантование с использованием глобального диапазона"""
        if global_max == global_min:
            return np.zeros_like(quant, dtype=np.float16)
        scale = (1 << self.qbits) - 1
        return quant.astype(np.float16) / scale * (global_max - global_min) + global_min

    def _low_rank_matrix(self, delta: np.ndarray) -> np.ndarray:
        U, s, Vt = np.linalg.svd(delta, full_matrices=False)
        return U[:, :self.rank] @ np.diag(s[:self.rank]) @ Vt[:self.rank, :]




# ---------------- клиент ----------------
if __name__ == '__main__':
    path = "new.jpg"
    exp = ExpLieSVDSingleCodec(h=0.01, rank=3, qbits=4, name="1")
    packed = exp.compress(path)
    with open(exp.name + ".exp", 'wb') as f:
        f.write(packed)
    decompress = exp.decompress(packed)
    with open(exp.name + "_rec.jpg", 'wb') as f:
        f.write(decompress)
    bpp, file_size = exp.get_metric()

    psnr = exp.psnr()
    print(f'  bpp     : {bpp:.3f}')
    print(f'  PSNR    : {psnr:.2f} dB')
    print(f'  Size    : {file_size} bytes')

