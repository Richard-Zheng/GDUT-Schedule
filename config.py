JXFWHost = "jxfw.gdut.edu.cn"

JXFWURL = f"https://{JXFWHost}/new/ssoLogin"
AuthURL = "http://authserver.gdut.edu.cn/authserver/login"
GetStudentCoursesDateURL = f"https://{JXFWHost}/xsgrkbcx!getKbRq.action" # xsgrkbcx: 学生个人课表查询

headers = {
    'Cache-Control': 'max-age=0',
    'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'Upgrade-Insecure-Requests': '1',
    'Origin': 'https://authserver.gdut.edu.cn',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Dest': 'document',
    'Referer': 'https://authserver.gdut.edu.cn/authserver/login?service=http%3A%2F%2Fjxfw.gdut.edu.cn%2Fnew%2FssoLogin',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

params = (
    ('service', JXFWURL),
)

"""节次时间"""
jc_to_time = {
    1: ['08:30', '09:15'],
    2: ['09:20', '10:05'],
    3: ['10:25', '11:10'],
    4: ['11:15', '12:00'],
    5: ['13:50', '14:35'],
    6: ['14:40', '15:25'],
    7: ['15:30', '16:15'],
    8: ['16:30', '17:15'],
    9: ['17:20', '18:05'],
    10: ['18:30', '19:15'],
    11: ['19:20', '20:05'],
    12: ['20:10', '20:55'],
}
