# AI Post Generator 🚀📸

## Proje Açıklaması
AI Post Generator, OpenAI ve Instagram API'lerini kullanarak otomatik içerik üreten bir Python uygulamasıdır.

## Özellikler
- 🎨 OpenAI DALL-E 3 ile yapay zeka görüntü üretimi
- 📱 Instagram'a otomatik post paylaşımı
- 🕒 Zamanlanmış içerik oluşturma

## Gereksinimler
- Python 3.10+
- Docker
- Docker Compose

## Kurulum

### 1. Yerel Geliştirme
```bash
git clone https://github.com/kullaniciadi/AIPostGenerator.git
cd AIPostGenerator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Docker ile Çalıştırma
```bash
docker-compose up --build
```

## Konfigürasyon
`.env` dosyasını düzenleyin:
```
OPENAI_API_KEY=your_openai_api_key
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
```

## Test
```bash
pytest tests/
```

## CI/CD
GitHub Actions ile otomatik test ve dağıtım yapılmaktadır.

## Lisans
MIT License
