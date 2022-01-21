from flask import Blueprint, render_template, request, g, redirect, url_for, jsonify

from apps.article.models import Article, Article_type, Comment
from apps.user.models import User
from apps.utils.util import user_type
from exts import db

article_bp = Blueprint('article', __name__, url_prefix='/article')


@article_bp.app_template_filter('cdecode')
def content_decode(content):
    content = content.decode('utf-8')
    return content


@article_bp.route('/publish', methods=['GET', 'POST'])
def publish_article():
    if request.method == 'POST':
        title = request.form.get('title')
        type_id = request.form.get('type')
        content = request.form.get('content')
        # uid = request.form.get('uid')
        article = Article()
        article.title = title
        article.content = content
        article.user_id = g.user.id
        article.type_id = type_id
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('user.index'))
    else:
        users = User.query.filter(User.isdelete == False).all()
        return render_template('article/add_article.html', users=users)


@article_bp.route('/all')
def all_article():
    articles = Article.query.all()
    return render_template('article/all.html', articles=articles)


@article_bp.route('/all1')
def all_article1():
    id = request.args.get('id')
    user = User.query.get(id)
    return render_template('article/all1.html', user=user)


@article_bp.route('/detail')
def article_detail():
    article_id = request.args.get('aid')
    article = Article.query.get(article_id)
    types = Article_type.query.all()
    id = request.cookies.get('uid', None)
    if id:
        user = User.query.get(id)
    page = int(request.args.get('page', 1))
    comments = Comment.query.filter(Comment.article_id == article_id) \
        .order_by(-Comment.cdatetime) \
        .paginate(page=page, per_page=5)

    return render_template('article/detail.html', article=article, types=types, user=user, comments=comments)
    # return render_template('article/detail.html', article=article, types=types, user=user)


@article_bp.route('/love')
def article_love():
    article_id = request.args.get('aid')
    tag = request.args.get('tag')
    article = Article.query.get(article_id)
    if tag == '1':
        article.love_num -= 1
    else:
        article.love_num += 1
    db.session.commit()
    return jsonify(num=article.love_num)


@article_bp.route('/add_comment', methods=['GET', 'POST'])
def article_comment():
    if request.method == 'POST':
        comment_content = request.form.get('comment')
        user_id = g.user.id
        article_id = request.form.get('aid')
        # 评论模型
        comment = Comment()
        comment.comment = comment_content
        comment.user_id = user_id
        comment.article_id = article_id
        db.session.add(comment)
        db.session.commit()

        return redirect(url_for('article.article_detail') + "?aid=" + article_id)
    return redirect(url_for('user.index'))


@article_bp.route('type_search')
def type_search():
    # 获取用户和文章类型给导航使用
    user, types = user_type()

    # tid的获取
    tid = request.args.get('tid', 1)
    page = int(request.args.get('page', 1))

    # 分页器？？？？
    # pagination对象
    articles = Article.query.filter(Article.type_id == tid).paginate(page=page, per_page=3)

    params = {
        'user': user,
        'types': types,
        'articles': articles,
        'tid': tid,
    }

    return render_template('article/article_type.html', **params)
