import os
import time
from flask import Flask, jsonify
from celery import Celery, current_task


app = Flask(__name__)
app.config.update(CELERY_CONFIG={
    'broker_url': os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
})
celery = Celery(app.import_name, broker='redis://redis:6379/0', backend='redis://redis:6379/0')


@celery.task
def simple_task(message):
    time.sleep(30)
    return {
        "message": message
    }


@celery.task
def simple_failed_task():
    raise Exception("Something really bad happened.")


@celery.task
def custom_metadata_task():
    time.sleep(15)
    current_task.update_state(
        state='STARTED',
        meta={
            'sleeping_15_sec': 'done', 
            'sleeping_30_sec': 'starting',
            'sleeping_10_sec': None
        }
    )
    time.sleep(30)
    current_task.update_state(
        state='STARTED',
        meta={
            'sleeping_15_sec': 'done', 
            'sleeping_30_sec': 'done',
            'sleeping_10_sec': 'starting'
        }
    )
    time.sleep(10)
    return {
        'sleeping_15_sec': 'done', 
        'sleeping_30_sec': 'done',
        'sleeping_10_sec': 'done',
        'total_sleeing_time': 55
    }


def get_celery_task_status(taskid):
    task_result = celery.AsyncResult(taskid)
    if task_result.state == 'FAILURE':
        result = {
            "task_id": taskid,
            "task_state": task_result.state,
            "task_result": str(task_result.result)
        }
    else:
        result = {
            "task_id": taskid,
            "task_state": task_result.state,
            "task_result": task_result.result
        }
    return result


@app.route('/', methods=['GET'])
def route_base():
    return 'Up and Running!'


@app.route('/simple-async', methods=['POST'])
def route_simple_async():
    task = simple_task.apply_async(args=["message at the end"])
    return jsonify({"task_id": task.id}), 202


@app.route('/simple-failed-async', methods=['POST'])
def route_failed_async():
    task = simple_failed_task.apply_async()
    return jsonify({"task_id": task.id}), 202


@app.route('/custom-metadata-async', methods=['POST'])
def route_custom_metadata():
    task = custom_metadata_task.apply_async()
    return jsonify({"task_id": task.id}), 202


@app.route('/status/<taskid>', methods=['GET'])
def route_task_status(taskid):
    result = get_celery_task_status(taskid)
    return jsonify(result), 200
