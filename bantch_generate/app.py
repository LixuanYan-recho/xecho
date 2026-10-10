from webapp import create_app
from webapp.config import DEBUG, HOST, PORT


app = create_app()


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)

#测试修改