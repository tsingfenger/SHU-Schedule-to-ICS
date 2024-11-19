import re
from datetime import datetime, timedelta
from ics import Calendar, Event
import requests
import rsa
import base64
from dotenv import load_dotenv
from pytz import timezone

load_dotenv()
_base_url = "https://jwxk.shu.edu.cn"
_schedule_list = "/xsxk/elective/shu/clazz/list"
_student_info = "/xsxk/web/studentInfo"
_key_str = ("-----BEGIN PUBLIC KEY-----\n"
            "        MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDl/aCgRl9f/4ON9MewoVnV58OL\n"
            "        OU2ALBi2FKc5yIsfSpivKxe7A6FitJjHva3WpM7gvVOinMehp6if2UNIkbaN+plW\n"
            "        f5IwqEVxsNZpeixc4GsbY9dXEk3WtRjwGSyDLySzEESH/kpJVoxO7ijRYqU+2oSR\n"
            "       wTBNePOk1H+LRQokgQIDAQAB\n"
            "        -----END PUBLIC KEY-----")

session = requests.Session()

def encrypt_passwd(passwd):
    public_key = rsa.PublicKey.load_pkcs1_openssl_pem(_key_str.encode("utf-8"))
    encrypted_passwd = base64.b64encode(rsa.encrypt(passwd.encode("utf-8"), public_key)).decode("utf-8")
    return encrypted_passwd


def login():
    try:
        _response = session.get(_base_url)
        if "oauth.shu.edu.cn" in _response.url:
            print("校园网连接正常")
            _username = input("请输入学号：")
            _encrypted_passwd = encrypt_passwd(input("请输入密码："))
            login_data = {"username": _username, "password": _encrypted_passwd}
            _response = session.post(_response.url, login_data)
            if "token" in _response.url:
                _token = _response.url[_response.url.index("?token=")+7:]
                return _token
            else:
                print("可能是账号或密码错误，请检查后重试")
                exit()
        else:
            print("无法定向到认证系统，请稍后再试")
            exit()
    except requests.exceptions.RequestException as e:
        print("无法访问选课系统，请检查是否拥有校园网访问权限。", e)
        exit()


def term_select(_token):
        _response = session.post(_base_url + _student_info, headers={"Authorization":_token})
        _elective_term = _response.json()["data"]["student"]["electiveBatchList"]
        if _elective_term:
            print("可选学期：")
            for i, term in enumerate(_elective_term):
                print(f'{i+1}. {term["name"]}')
            i = int(input("请输入需导出学期前的序号: ")) - 1
            if _elective_term[i]:
                print(f'您选择的学期为{_elective_term[i]["name"]}')
                code = _elective_term[i]["code"]
                begin_time = input("请输入本学期开始时间（第一周周一），格式如'2024-11-18': ")
                if re.match(r'^\d+-\d+-\d+$', begin_time):
                    return _elective_term[i]["name"], code, begin_time
                else:
                    print("日期格式错误")
                    exit()
            else:
                print("所选学期无效")
                exit()
        else:
            print("当前无可选学期。")
            exit()


def get_schedule(code, _token):
    header = {
        "Authorization": _token,
        "Batchid": code
    }
    data = {
        "teachingClassType": "XGKC",
        "pageNumber": 1,
        "pageSize": 10,
        "orderBy": None
    }
    r = session.post(_base_url+_schedule_list, headers=header, data=data)
    student_schedule = r.json()["data"]
    schedule=[]
    for course in student_schedule["xskb"]:
        place = ""
        for table in student_schedule["yxkc"]:
            if table["CODE"] == course["CODE"]:
                place = table["teachingPlaceHide"]
        schedule.append({"code":course["CODE"], "name":course["KCM"], "week":course["SKZCMC"],
                         "day":course["SKXQ"], "start":course["KSJC"], "end":course["JSJC"],
                         "teacher":course["SKJS"], "place":place})
    print("识别到以下课程(出现重复是正常的)：")
    for course in schedule:
        print(course["name"], end=", ")
    print()
    return schedule


def map_time(schedule):
    time_dic = [["8:00", "8:45"], ["8:55", "9:40"], ["10:00", "10:45"], ["10:55", "11:40"],
                ["13:00", "13:45"], ["13:55", "14:40"], ["15:00", "15:45"], ["15:55", "16:40"],
                ["18:00", "18:45"], ["18:55", "19:40"], ["20:00", "20:45"], ["20:55", "21:40"]]
    for course in schedule:
        course["week"] = course["week"].replace("周", "")
        if "," in course["week"]:
            course["week"] = [int(x) for x in course["week"].split(",")]
        elif "单" in course["week"]:
            course["week"] = course["week"].replace("(单)", "")
            course["week"] = course["week"].split("-")
            course["week"] = [x for x in range(int(course["week"][0]), int(course["week"][1]) + 1, 2)]
        elif "双" in course["week"]:
            course["week"] = course["week"].replace("(双)", "")
            course["week"] = course["week"].split("-")
            course["week"] = [x for x in range(int(course["week"][0]) + 1, int(course["week"][1]) + 1, 2)]
        else:
            course["week"] = course["week"].split("-")
            course["week"] = [x for x in range(int(course["week"][0]), int(course["week"][1]) + 1)]
        course["start"] = time_dic[int(course["start"]) - 1][0]
        course["end"] = time_dic[int(course["end"]) - 1][1]
    return schedule


def save_icl(schedule, begin_time, name):
    calendar = Calendar()
    for course in schedule:
        for week in course["week"]:
            event = Event()
            start_hour, start_minute = course["start"].split(":")
            end_hour, end_minute = course["end"].split(":")
            event.name = course["name"]
            event_begin = begin_time + timedelta(weeks = int(week) - 1, days = int(course["day"])-1, hours=int(start_hour), minutes=int(start_minute))
            event_end = begin_time + timedelta(weeks = int(week) - 1, days = int(course["day"])-1, hours=int(end_hour), minutes=int(end_minute))
            event.begin = event_begin.astimezone(timezone('Asia/Shanghai'))
            event.end = event_end.astimezone(timezone('Asia/Shanghai'))
            event.description = course["teacher"]
            event.location = course["place"]
            calendar.events.add(event)
            '''print(course["name"], begin_time + timedelta(weeks = int(week) - 1, days = int(course["day"])-1, hours=int(start_hour), minutes=int(start_minute)),
                  begin_time + timedelta(weeks = int(week) - 1, days = int(course["day"])-1, hours=int(end_hour), minutes=int(end_minute)),
                  course["teacher"], course["place"])'''
    with open(f'{name}.ics', 'w', encoding='utf-8') as f:
        f.writelines(calendar)
        print(f'日历文件"{name}.ics"已保存至当前目录下，请仔细核对日程是否正确。')
    return 0


def main():
    token = login()
    name, code, begin_time = term_select(token)
    begin_date = datetime.strptime(begin_time, "%Y-%m-%d")
    student_schedule = get_schedule(code, token)
    schedule = map_time(student_schedule)
    save_icl(schedule, begin_date, name)


if __name__ == "__main__":
    main()
    input("按下任意键以退出...")