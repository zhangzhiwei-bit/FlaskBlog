import hashlib

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from apps.article.models import Article_type, Article
from settings import Config
from apps.user.models import User, Aboutme, MessageBoard
from exts import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

required_login_list = ['/user/center',
                       '/user/change',
                       '/article/publish',
                       '/user/upload_photo',
                       '/article/add_comment',
                       '/user/aboutme',
                       '/user/showabout']


# 自定义一个过滤器
@user_bp.app_template_filter('cdecode')
def content_decode(content):
    content = content.decode('utf-8')
    return content[:2000]


@user_bp.app_template_filter('cdecode1')
def content_decode1(content):
    content = content.decode('utf-8')
    return content


@user_bp.before_app_first_request
def first_request():
    print('before app first request')


@user_bp.before_app_request
def before_request():
    if request.path in required_login_list:
        id = request.cookies.get('uid', None)
        if not id:
            return render_template('user/login.html')
        else:
            user = User.query.get(id)
            g.user = user


@user_bp.after_app_request
def after_request_test(response):
    return response


@user_bp.teardown_app_request
def teardown_request_test(response):
    return response


@user_bp.route('/')
def index():
    uid = request.cookies.get('uid', None)  # 没有取到默认值为空
    page = int(request.args.get('page', 1))
    pagination = Article.query.order_by(-Article.pdatetime).paginate(page=page, per_page=4)
    types = Article_type.query.all()
    if uid:
        user = User.query.get(uid)
        return render_template('user/index.html', user=user, pagination=pagination, types=types)
    else:
        return render_template('user/index.html', pagination=pagination, types=types)


@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')
        phone = request.form.get('phone')
        email = request.form.get('email')
        if password == repassword:
            # 与模型结合进行插入数据库
            user = User()
            user.username = username
            # user.password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            user.password = generate_password_hash(password)
            user.phone = phone
            user.email = email
            # 添加
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('user.index'))
        else:
            return '两次密码不一致'

    return render_template('user/register.html')


@user_bp.route('/checkphone', methods=['GET', 'POST'])
def check_phone():
    phone = request.args.get('phone')
    user = User.query.filter(User.phone == phone).all()
    if user:
        return jsonify(code=400, msg='此号码已被注册')
    else:
        return jsonify(code=200, msg='此号码可用')


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        users = User.query.filter(User.username == username).all()
        for user in users:
            flag = check_password_hash(user.password, password)
            if flag:
                # session['uid']=user.id
                response = redirect((url_for('user.index')))
                response.set_cookie('uid', str(user.id), max_age=1800)
                return response
        return render_template('user/login.html', msg='用户名或者密码有误')
    return render_template('user/login.html')


@user_bp.route('/logout')
def logout():
    response = redirect((url_for('user.index')))
    response.delete_cookie('uid')
    return response


# 用户中心
@user_bp.route('/center')
def user_center():
    types = Article_type.query.all()
    return render_template('user/center.html', user=g.user, types=types)


ALLOWED_EXTENSIONS = ['jpg', 'png', 'gif', 'bmp', 'jepg']


@user_bp.route('/change', methods=['GET', 'POST'])
def user_change():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        email = request.form.get('email')
        # 获取文件
        icon = request.files.get('icon')
        icon_name = icon.filename
        suffix = icon_name.rsplit('.')[-1]
        if suffix in ALLOWED_EXTENSIONS:
            icon_name = secure_filename(icon_name)
            file_path = os.path.join(Config.UPLOAD_ICON_DIR, icon_name)
            icon.save(file_path)
            user = g.user
            user.username = username
            user.phone = phone
            user.email = email
            path = 'upload/icon/'
            user.icon = path + icon_name
            print(user.icon)
            db.session.commit()
            return render_template('user/center.html', user=g.user)
        else:
            return render_template('user/center.html', user=g.user, msg='图片格式不正确')

    return render_template('user/center.html', user=g.user)


@user_bp.route('/upload_photo', methods=['GET', 'POST'])
def upload_photo():
    photo = request.files.get('photo')


@user_bp.route('/aboutme', methods=['GET', 'POST'])
def about_me():
    content = request.form.get('about')
    aboutme = Aboutme()
    aboutme.content = content.encode('utf-8')
    aboutme.user_id = g.user.id
    db.session.add(aboutme)
    db.session.commit()
    return render_template('user/aboutme.html', user=g.user)


@user_bp.route('/showabout')
def show_about():
    return render_template('user/aboutme.html', user=g.user)


@user_bp.route('/board', methods=['GET', 'POST'])
def show_board():
    uid = request.cookies.get('uid', None)
    user = None
    if uid:
        user = User.query.get(uid)
    page = int(request.args.get('page',1))
    boards = MessageBoard.query.order_by(-MessageBoard.mdatetime).paginate(page=page, per_page=5)
    if request.method == 'POST':
        content = request.form.get('board')
        msg_board = MessageBoard()
        msg_board.content = content
        if uid:
            msg_board.user_id = uid
        db.session.add(msg_board)
        db.session.commit()
        return redirect(url_for('user.show_board'))
    return render_template('user/board.html',user=user, boards=boards)

@user_bp.route('/board_del')
def delete_board():
    bid=request.args.get('bid')
    if bid:
        msgboard=MessageBoard.query.get(bid)
        db.session.delete(msgboard)
        db.session.commit()
        return redirect(url_for('user.show_board'))