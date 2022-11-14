import datetime , calendar , os
from sqlalchemy import extract,func
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask,request,render_template,redirect, url_for
from flask import current_app as app
from .models import *

@app.route('/', methods=['GET','POST'])
def home():
    return render_template('home.html')
    

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='GET':
        return render_template("login.html")
    if request.method == 'POST':
        name = request.form.get('name')
        existing_user = user.query.filter(user.user_name == request.form.get('name'),\
                user.password==request.form.get('pass')).all()
        if existing_user == []:
            return render_template('error.html')
        else:
            return redirect('/userpage/'+name)

@app.route('/signup', methods=['GET','POST'])
def signup():  
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        new_user = user(user_name =  request.form.get('cname'), password = request.form.get('cpass'))
        db.session.add(new_user)
        db.session.commit()
        return redirect('/userpage/' + request.form.get('cname') )
    
@app.route('/userpage/<string:name>', methods= ['GET', 'POST'])
def userpage(name):
    if request.method == 'GET':
        tracker_list = []

        current_user = user.query.filter(user.user_name == name).first()
        assignment_list = assignment.query.filter(assignment.user_id == current_user.user_id).all()
        for i in assignment_list:
            current_tracker = tracker.query.filter(tracker.tracker_id == i.tracker_id).first()
            tracker_list.append(current_tracker)
         
        available_trackers = tracker.query.filter().all()

        return render_template('userpage.html', name = name, tracker_list = list(set(tracker_list)),available_trackers = available_trackers)
    
def new(x,y,days):
    newy = [[] for i in range(days)]
    for i in range(x.shape[0]):
        newy[x[i]].append(int(y[i])) 
    for i in range(len(newy)):
        if newy[i]:
            newy[i] = sum(newy[i])/len(newy[i])
        else:
            newy[i]=0
    y = np.array(newy)
    return y
def saveplot(y):
    fig = plt.figure()
    plt.plot(range(1,len(y)+1),y)
    plt.savefig('static/trendline.jpg')
    return

@app.route('/tracker/<string:name>/<string:tracker_name>',methods = ['GET','POST'])      
def tracker_logs(name,tracker_name):
    if request.method == 'GET':
        logs_list = []
        current_user = user.query.filter(user.user_name == name).first()
        current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
        assignment_list = assignment.query.filter(assignment.tracker_id == current_tracker.tracker_id, \
                                                    assignment.user_id == current_user.user_id).all()
        for i in assignment_list:
            dic = logs.query.filter(logs.log_id == i.log_id).first().__dict__
            dic['datetime'] =dic['datetime'][:16]
            dic = [dic['datetime'],dic['value'],dic['notes'],dic['log_id']]
            logs_list.append(dic)
        return render_template('logs.html', logs_list = logs_list, \
                                tracker_name = tracker_name, \
                                current_tracker = current_tracker,\
                                name = name)
    if request.method == 'POST':
        current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
        current_user = user.query.filter(user.user_name==name).first()
        period = int(request.form.get('period'))
        current_time = datetime.datetime.now()
        logs_thisyear = logs.query.filter(extract('year',logs.datetime) == current_time.year)
        logs_thismonth = logs_thisyear.filter(extract('month',logs.datetime) == current_time.month)
        logs_thisweek = logs_thismonth.filter(extract('week',func.date(logs.datetime))== current_time.isocalendar().week)
        logs_today = logs_thisweek.filter(extract('day',logs.datetime) == current_time.day)
        time_period = [logs_today,logs_thisweek,logs_thismonth]
        logs_list = []
        logs_intime = time_period[period].filter(logs.log_id == assignment.log_id).\
            filter(assignment.tracker_id==current_tracker.tracker_id)\
                .filter(assignment.user_id==current_user.user_id).all()
        x,y = [],[]
        for i in logs_intime:
            dic = i.__dict__
            x.append(datetime.datetime.strptime(i.datetime[:16],"%Y-%m-%d %H:%M"))
            y.append(i.value)
            dic['datetime'] =dic['datetime'][:16]
            dic = [dic['datetime'],dic['value'],dic['notes'],dic['log_id']]
            logs_list.append(dic)
        print(logs_list)
        if current_tracker.tracker_type == 'numeric':
            x = np.array(x)
            y = np.array(y)
            if period == 0:
                midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                if x.shape[0]:
                    x = np.apply_along_axis(lambda z:z[0].seconds//60,axis=1,arr=(x-midnight).reshape(-1,1))
                    y = new(x,y,60*24)
                    saveplot(y)
                else:
                    saveplot([0 for i in range(60*24)])
            if period == 1:
                if x.shape[0]:
                    weekstart = current_time-datetime.timedelta(days=current_time.weekday())
                    x = np.apply_along_axis(lambda z :z[0].days,axis=1, arr = (x-weekstart).reshape(-1,1))
                    y = new(x,y,7)
                    print(y)
                    saveplot(y)
                else:
                    saveplot([0 for i in range(7)])
                
            if period ==2:
                if x.shape[0]:
                    x = np.apply_along_axis(lambda z:z[0].day-1,axis=1,arr=(x).reshape(-1,1))
                    y = new(x,y,calendar.monthrange(current_time.year, current_time.month)[1])
                    saveplot(y)
                else:
                    saveplot([0 for i in range(calendar.monthrange(current_time.year, current_time.month)[1])])
                    
        return render_template('logs.html', logs_list = logs_list, \
                                tracker_name = tracker_name,\
                                name = name, current_tracker=current_tracker, p = True)
        
        
@app.context_processor
def override_url_for():
    """
    Generate a new token on every request to prevent the browser from
    caching static files.
    """
    return dict(url_for=dated_url_for)


def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)    
    

@app.route('/tracker/add/<string:name>',  methods= ['GET', 'POST'])      
def add_tracker(name):
    if request.method == 'GET':
        return render_template('tracker_add.html', name = name)
    
    
    if request.method == "POST":
        tracker_name = request.form.get('tname')
        trackers_list = tracker.query.filter(tracker.tracker_name).all()
        if tracker_name in trackers_list:
            return redirect('/tracker/' + tracker_name + '/add/' + name)
        else:
            new_tracker = tracker(tracker_name = request.form.get('tname'), \
                                tracker_type = request.form.get('ttype'), \
                                tracker_settings = request.form.get('tsettings'))
            
       
        db.session.add(new_tracker)
        new_assignment = assignment()
        db.session.commit()
        return redirect('/tracker/' + tracker_name + '/add/' + name)

@app.route('/tracker/<string:tracker_name>/delete/<string:name>',  methods= ['GET', 'POST'])      
def delete_tracker(name, tracker_name):
    current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
    current_user = user.query.filter(user.user_name == name).first()
    asn_deleted = assignment.query.filter(assignment.user_id == current_user.user_id).\
                                filter(assignment.tracker_id == current_tracker.tracker_id).delete()
    db.session.commit()
    return redirect('/userpage/' + name)

@app.route('/tracker/<string:tracker_name>/add/<string:name>', methods = ['GET', 'POST'])    
def log(tracker_name, name):
    current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
    current_user = user.query.filter(user.user_name == name).first()
    
    if request.method == "GET":
        
        current_time = datetime.datetime.now()
        current_datetime = current_time.strftime ("%Y-%m-%dT%H:%M")
     
        return render_template('log_add.html',tracker_name = tracker_name, \
                                current_tracker = current_tracker, \
                                name = name, current_datetime = current_datetime)
        
    if request.method == 'POST':
        current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
       
        d = request.form.get('datetime').replace('T',' ')
        dtime = datetime.datetime.strptime(d, "%Y-%m-%d %H:%M")

        value = request.form.get('value')
        if int(value)>70 and int(value)<90:
            
            new_log = logs(datetime = dtime.replace(second = 0),\
                        value = request.form.get('value'),\
                        notes =request.form.get('notes'))
            db.session.add(new_log)
            db.session.commit()
            new_assignment = assignment(tracker_id = current_tracker.tracker_id,\
                                user_id = current_user.user_id,\
                                log_id = new_log.log_id)
            db.session.add(new_assignment)
            db.session.commit()
            return redirect('/tracker/' + name + '/' + current_tracker.tracker_name)
        else:
            return render_template('value_error.html')
        
@app.route('/tracker/<string:tracker_name>/delete/<int:log_id>/<string:name>', methods = ['GET', 'POST'])    
def log_delete(tracker_name, name,log_id):
    logs.query.filter(logs.log_id == log_id).delete()
    assignment.query.filter(assignment.log_id == log_id).delete()
    db.session.commit()
    return redirect('/tracker/'+ name+'/' + tracker_name)

@app.route('/tracker/<string:tracker_name>/edit/<int:log_id>/<string:name>',methods = ['GET', 'POST']) 
def log_edit(tracker_name, name, log_id):
    if request.method == 'GET':
        current_log = logs.query.filter(logs.log_id == log_id).first()
        current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
        print(current_log.value,current_log.notes)
        return render_template('log_edit.html',current_tracker=current_tracker, current_log = current_log, \
                                tracker_name = tracker_name, \
                                name=name, log_id = log_id, log_time = current_log.datetime.replace(" ","T"))
        # return render_template('log_edit.html')
    if request.method == 'POST':
        current_log = logs.query.filter(logs.log_id == log_id).first()
        current_log.datetime = request.form.get('datetime')
        current_log.value = request.form.get('value')
        current_log.notes = request.form.get('notes')
        db.session.add(current_log)
        db.session.commit()
        return redirect('/tracker/' + name +'/'+ tracker_name)