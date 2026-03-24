import time
import multiprocessing
import flama
from flama import Flama, background
from flama.http import JSONResponse

app = Flama()


def blocking_io_task(email: str):
    print(f"[Thread] ⏳ Starting email to {email}...")
    time.sleep(2)
    print(f"[Thread] ✅ Email sent to {email}!")


def cpu_heavy_task(data_id: int):
    pid = multiprocessing.current_process().pid
    print(f"[Process] ⚙️  Processing data {data_id} on PID {pid}...")
    _ = sum(i * i for i in range(10_000_000))
    print(f"[Process] ✅ Data {data_id} processed!")


@app.route("/thread/")
async def thread():
    task = background.BackgroundThreadTask(blocking_io_task, "user@example.com")
    return JSONResponse(
        {"status": "queued", "message": "Email is sending in background"},
        background=task,
    )


@app.route("/process/")
async def process():
    task = background.BackgroundProcessTask(cpu_heavy_task, 101)
    return JSONResponse(
        {"status": "queued", "message": "Heavy calculation started"}, background=task
    )


if __name__ == "__main__":
    flama.run(flama_app=app, server_host="0.0.0.0", server_port=8000)
