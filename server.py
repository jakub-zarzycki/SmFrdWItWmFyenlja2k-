from sanic import Sanic
from sanic import exceptions
from sanic import response
from sanic.response import json

from worker import worker

server = Sanic()
server.config.REQUEST_MAX_SIZE = 1024 * 1024 #limit requests to 1 MB = 2^^20 B
server.config.KEEP_ALIVE = 0

#it should have been database but i had not enough time
#data_by_url = {"id" : int, "interval" : int}
data_by_url = dict()

#maps ids to urls
#data_by_id = {"url" : string}
data_by_id = dict()

#we need to be able to access workers
workers_by_id = dict()

id = 0

@server.route('/api/fetcher', methods=["POST", "GET", "DELETE"])
def fetcher(request):

    global id

    if request.method == "GET":
        urls = []
        for id in data_by_id:
            _, interval = data_by_url[data_by_id[id]]
            urls.append({"id":id, "url":data_by_id[id], "interval":interval})

        return json(body=urls)

    try:
        new_data = request.json

    except exceptions.InvalidUsage:
        return response.html(body="", status=400)

    try:
        url_id, _ = data_by_url[new_data['url']]
        data_by_url[new_data['url']] = (url_id, new_data['interval'])

    except KeyError:
        id += 1
        data_by_url[new_data['url']] = (id, new_data['interval'])
        data_by_id[id] = new_data['url']
        url_id = id

    new_worker = worker(id, new_data['url'], new_data['interval'])
    workers_by_id[url_id] = new_worker
    new_worker.work()

    return json({'id':url_id})

@server.route('/api/fetcher/<id:int>', methods=["DELETE", "GET"])
def remove(request, id):

    if request.method == "GET":
        return response.html(body="", status=400)

    try:
        url = data_by_id[id]
        data_by_url.pop(url)
        data_by_id.pop(id)

    except KeyError:
        return response.html(body="", status=200)

    workers_by_id[id].stop()
    workers_by_id.pop(id)

    return response.html(body="")

@server.route('/api/fetcher/<id:int>/history', methods=["GET",])
def history(request, id):

    # check if key exists
    try:
        worker = workers_by_id[id]

    except KeyError:
        return response.html(body="", status=404)

    history = worker.history

    return response.text(body=history)

@server.route('/api/fetcher/<id>/history')
def history(request, id):

    return response.html(body="", status=400)

if __name__ == '__main__':
    server.run(host='0.0.0.0', port=8080)
