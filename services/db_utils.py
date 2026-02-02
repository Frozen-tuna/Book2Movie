from tinydb import Query

def fetch_json(object_name, db):
    Q = Query()
    if db.contains(Q.name == object_name):
        return db.get(Q.name == object_name)["data"]
    else:
        return None


def upsert_json(object_name, data, db):
    Q = Query()
    db.upsert({"name": object_name, "data": data}, Q.name == object_name)


def fetch_status(start, stop, db):
    Q = Query()
    if db.contains(Q.name == "status" and Q.start == start and Q.stop == stop):
        return db.get(Q.name == "status" and Q.start == start and Q.stop == stop)["data"]
    else:
        return {
            "text": False,
            "characters": False,
            "quotes": False,
            "character_voices": False,
            "voiced_quotes": False,
            "sound": False,
            "image_prompts": False,
            "images": False,
        }


def upsert_status(status, stage, start, stop, db):
    Q = Query()
    status[stage] = True

    db.upsert(
        {"name": "status", "data": status, "start": start, "stop": stop},
        (Q.name == "status") & (Q.start == start) & (Q.stop == stop),
    )