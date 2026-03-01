import asyncio
import aiohttp
import simpleaudio as sa
import io

# 假设这是您的API请求函数
async def fetch_audio(text):
    audio_generation_url = "http://localhost:3752/"
    data = {
        "text": text,
        "text_language": "zh"
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(audio_generation_url, json=data) as response:
            if response.status == 200:
                return io.BytesIO(await response.read())
            else:
                print("API请求失败，状态码：", response.status)
                return None

# 假设这是您的播放函数
def play_audio(audio_data):
    if audio_data:
        audio_wave_obj = sa.WaveObject.from_wave_file(audio_data)
        play_obj = audio_wave_obj.play()
        play_obj.wait_done()

# 主程序
async def main():
    text = "这是一个晴朗的早晨"
    audio_data = await fetch_audio(text)
    if audio_data:
        # 使用asyncio.create_task创建一个新的异步任务来播放音频
        loop = asyncio.get_event_loop()
        loop.create_task(play_audio(audio_data))

# 主程序
async def main():
    text = "这是一个晴朗的早晨"
    audio_data = await fetch_audio(text)
    if audio_data:
        play_audio(audio_data)


# 运行主程序
asyncio.run(main())
