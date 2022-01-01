from handler import hello
import json
test_data = {
    'Records': [
        {
            'body': json.dumps({
                'address': 'FcadjtVVBLfP5Lp4NnGFZLLcqdoMgUwYT7MV6yvUdhmq',
                'name': 'rahul gandhi',
                'count': 1,
                'twitter_uid': '620896033'
            })
        }
    ]
}

hello(test_data, None)