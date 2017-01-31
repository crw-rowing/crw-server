import database
import crw
import crw_jsonrpc
import datetime as dt
import random as r

main_users = [
    'lotte@mail.com',
    'luuk@mail.com',
    'nikita@mail.com',
    'justin@mail.com',
    'ruud@mail.com',
    'marien@mail.com']

secundary_users = ['{}@mail.com'.format(i) for i in range(1, 20)]

all_users = main_users + secundary_users


def create_fake_data(user, user_id, rpc):
    hr_base = r.randint(80, 95)
    hr_dev = r.randint(5, 15)

    weight_base = r.randint(60, 85)
    weight_dev = r.randint(2, 4)

    power_base = r.randint(300, 500)
    power_dev = r.randint(50, 100)

    for i in range(0, 70):
        date = dt.date.today() - dt.timedelta(days=i)

        rpc.authenticated = True
        rpc.current_user_id = user_id
        rpc.add_health_data(date,
                            hr_base + int(r.random() * hr_dev),
                            weight_base + int(r.random() * weight_dev),
                            '')

        time = dt.time(r.randint(8, 16))
        rpc.authenticated = True
        rpc.current_user_id = user_id
        rpc.add_training(dt.datetime.combine(date, time),
                         r.randint(0, 1) == 0,
                         '',
                         [(r.randint(100, 500), power_base +
                           int(r.random() * power_dev),
                           r.randint(20, 40),
                           dt.timedelta(seconds=r.randint(30, 300)))])

if __name__ == '__main__':
    db = database.Database(crw.DATABASE_HOST, crw.DATABASE_PORT,
                           crw.DATABASE_NAME,
                           crw.DATABASE_USER, crw.DATABASE_PASS)
    rpc = crw_jsonrpc.CrwJsonRpc(db)
    udb = database.UserDatabase(db)
    tdb = database.TeamDatabase(db)

    i = 1
    for user in all_users:
        rpc.create_account(user, 'test')
        create_fake_data(user, i, rpc)
        i += 1

    tdb.create_team(1, 'Team crw')
    for i in range(2, 7):
        tdb.add_user_to_team(1, i)
