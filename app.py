from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder=".")
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///tasks.db"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "ログインしてください"


class User(UserMixin, db.Model):
    id = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(200), nullable=False)
    lastname = db.Column(db.String(80))
    firstname = db.Column(db.String(80))
    email = db.Column(db.String(120))
    timing_hours = db.Column(db.Integer, default=0)
    timing_minutes = db.Column(db.Integer, default=0)
    tasks = db.relationship("Task", backref="user", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.String(50))
    is_shared = db.Column(db.Boolean, default=False)
    my_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.String(50))
    user_id = db.Column(db.String(80), db.ForeignKey("user.id"), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route("/")
@login_required
def index():
    my_tasks = Task.query.filter_by(user_id=current_user.id).all()
    shared_tasks = Task.query.filter(Task.user_id != current_user.id, Task.is_shared == True).all()
    my_favorite_tasks = Task.query.filter_by(user_id=current_user.id, my_favorite=True).all()
    return render_template("index.html", title="タスク一覧",
                           my_tasks=my_tasks, shared_tasks=shared_tasks,
                           my_favorite_tasks=my_favorite_tasks)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.get(request.form.get("id"))
        if user and check_password_hash(user.password, request.form.get("password")):
            login_user(user)
            return redirect(url_for("index"))
        flash("ユーザIDまたはパスワードが間違っています")
    return render_template("login.html", title="ログイン")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uid = request.form.get("id")
        if User.query.get(uid):
            flash("そのユーザIDは既に使われています")
            return redirect(url_for("register"))
        user = User(
            id=uid,
            password=generate_password_hash(request.form.get("password")),
            lastname=request.form.get("lastname"),
            firstname=request.form.get("firstname"),
            email=request.form.get("email", ""),
        )
        db.session.add(user)
        db.session.commit()
        flash("登録が完了しました。ログインしてください")
        return redirect(url_for("login"))
    return render_template("register.html", title="新規ユーザ登録")


@app.route("/create", methods=["POST"])
@login_required
def create():
    task = Task(
        name=request.form.get("name"),
        deadline=request.form.get("deadline"),
        is_shared="is_shared" in request.form,
        my_favorite="my_favorite" in request.form,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        user_id=current_user.id,
    )
    db.session.add(task)
    db.session.commit()
    flash("タスクを作成しました")
    return redirect(url_for("index"))


@app.route("/update", methods=["GET", "POST"])
@login_required
def update():
    my_tasks = Task.query.filter_by(user_id=current_user.id).all()
    if request.method == "POST":
        for task in my_tasks:
            task.name = request.form.get(f"name_{task.id}", task.name)
            task.deadline = request.form.get(f"deadline_{task.id}", task.deadline)
            task.is_shared = f"is_shared_{task.id}" in request.form
            task.my_favorite = f"my_favorite_{task.id}" in request.form
        db.session.commit()
        flash("タスクを更新しました")
        return redirect(url_for("index"))
    return render_template("update.html", title="タスク更新", my_tasks=my_tasks)


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    my_tasks = Task.query.filter_by(user_id=current_user.id).all()
    if request.method == "POST":
        ids = request.form.getlist("delete")
        Task.query.filter(Task.id.in_(ids)).delete()
        db.session.commit()
        flash("タスクを削除しました")
        return redirect(url_for("index"))
    return render_template("delete.html", title="タスク削除", my_tasks=my_tasks)


@app.route("/remind_setting", methods=["GET", "POST"])
@login_required
def remind_setting():
    if request.method == "POST":
        current_user.email = request.form.get("email", "")
        current_user.timing_hours = int(request.form.get("timing_hours", 0))
        current_user.timing_minutes = int(request.form.get("timing_minutes", 0))
        db.session.commit()
        flash("リマインダー設定を更新しました")
        return redirect(url_for("index"))
    return render_template("remind_setting.html", title="リマインダー設定", user=current_user)


@app.route("/account_delete", methods=["GET", "POST"])
def account_delete():
    if request.method == "POST":
        user = User.query.get(request.form.get("id"))
        if user and check_password_hash(user.password, request.form.get("password")):
            Task.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()
            flash("アカウントを削除しました")
            return redirect(url_for("login"))
        flash("ユーザIDまたはパスワードが間違っています")
    return render_template("account_delete.html", title="アカウント削除")


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
