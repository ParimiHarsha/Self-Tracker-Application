from os import stat
from turtle import st
from xmlrpc.client import Marshaller
from flask import make_response, request
from flask_restful import Resource, Api, marshal_with, fields
from sqlalchemy import desc
from .database import db 
from .models import *
from werkzeug.exceptions import HTTPException
import json

class DefaultError(HTTPException):
    def __init__(self, status_code, desc):
        self.response = make_response('', status_code)
        self.description = "<p>"+desc+"</p>"

class Success(HTTPException):
    def __init__(self, status_code, msg):
        self.response = make_response(msg, status_code)

class BError(HTTPException):
    def __init__(self, status_code, errorcode, errormsg):
        message = {
  "error_code": errorcode,
  "error_message": errormsg
}
        self.response = make_response(json.dumps(message), status_code)

loginfo = {
    "datetime" : fields.String,
    "value" : fields.Integer,
    "notes" : fields.String
}
trackerinfo = {
    "tracker_name": fields.String,
    "tracker_type": fields.String,
    "tracker_settings": fields.String,
}
types = set(['numeric','multiple choice','other'])

class Users(Resource):
    def get(self, name):
        try:
            tracker_list = []
            current_user = user.query.filter(user.user_name == name).first()
        except:
            raise DefaultError(status_code=500, description='Internal Server Error ')
        if current_user:
            assignment_list = assignment.query.filter(assignment.user_id == current_user.user_id).all()
            if assignment_list:
                for i in assignment_list:
                    current_tracker = tracker.query.filter(tracker.tracker_id == i.tracker_id).first()
                    tracker_list.append(current_tracker.tracker_name)
                tracker_list = list(set(tracker_list))
                return {"trackers": tracker_list} 
            else:
                raise DefaultError(status_code=404, desc="No trackers found for the given user\n")

        else:
            raise DefaultError(status_code=404, desc="User doesn't exist.\n")

class Trackers(Resource):
    @marshal_with(trackerinfo)
    def post(self):
        details = request.get_json()
        for i in trackerinfo.keys():
            if i not in details.keys():
                raise BError(status_code=400,errorcode="FLDSABSNT", errormsg="All the relevant details needed for a tracker must be provided.")
            if i == "tracker_settings":
                if type(details[i]) is list or not details[i]:
                    for j in details[i]:
                        if type(j) is not str:
                            raise BError(status_code=400, errorcode="BADINP", errormsg="All the settings must be strings")
                else:
                    raise BError(status_code=400, errorcode="BADINP", errormsg="The settings must be an array of strings")
            elif type(details[i]) is not str or details[i] == "":
                raise BError(status_code=400, errorcode="BADINP", errormsg=i + " must be a string and should not be empty")
            if i == "tracker_type" and details[i] not in types:
                raise BError(status_code=400, errorcode="BADTYPE", errormsg="The following is not a valid type of tracker")

        present = tracker.query.filter(tracker.tracker_name == details["tracker_name"]).all()
        if not present:
            new_tracker = tracker(tracker_name = details["tracker_name"], \
                              tracker_type = details["tracker_type"], \
                              tracker_settings = "tracker_settings")
            db.session.add(new_tracker)
            db.session.commit()
            return new_tracker
        else:
            raise BError(status_code=400,errorcode="DUP", errormsg="There already exists a tracker with the given name")

class Logs(Resource):
    @marshal_with(loginfo)
    def get(self, name, tracker_name):
        try:
            logs_list = []
            current_user = user.query.filter(user.user_name == name).first()
            current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
        except:
            raise DefaultError(status_code=500, description='Internal Server Error ')
        if current_user and current_tracker:
            assignment_list = assignment.query.filter(assignment.tracker_id == current_tracker.tracker_id, \
                                                assignment.user_id == current_user.user_id).all()
            for i in assignment_list:
                logs_list.append(logs.query.filter(logs.log_id == i.log_id).first())

            return logs_list
        else:
            d ="" 
            if not current_user:
                d = d+ "User doesn't exist.\n"
            elif not current_tracker:
                d = d+ "Tracker doesn't exist.\n"
            raise DefaultError(status_code=404, desc=d)
    
    @marshal_with(loginfo)
    def post(self,tracker_name, name):
        try:
            current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
            current_user = user.query.filter(user.user_name == name).first()
            details = request.get_json()
        except:
            raise DefaultError(status_code=500)
        for i in loginfo.keys():
            if i not in details.keys():
                raise BError(status_code=400,errorcode="FLDSABSNT", errormsg="All the relevant details needed for a tracker must be provided.")
            if i == 'notes':
                pass
            elif type(details[i]) is not str or details[i] == "":
                raise BError(status_code=400, errorcode="BADINP", errormsg=i + " must be a string and should not be empty")
        if current_user and current_tracker:
            new_log = logs(datetime = details['datetime'],\
                        value = details['value'],\
                        notes = details['notes'])
            db.session.add(new_log)
            db.session.commit()
            new_assignment = assignment(tracker_id = current_tracker.tracker_id,\
                                user_id = current_user.user_id,\
                                log_id = new_log.log_id)
            db.session.add(new_assignment)
            db.session.commit()
            return new_log
        else:
            d ="" 
            if not current_user:
                d = d+ "User doesn't exist.\n"
            elif not current_tracker:
                d = d+ "Tracker doesn't exist.\n"
            raise DefaultError(status_code=404, desc=d)

   
    # @marshal_with(loginfo)
    # def put(self, course_id):
    #     pass
        # try:
        #     oldentry = course.query.filter(course.course_id==course_id).first()
        # except:
        #     raise DefaultError(status_code=500)
        # if oldentry:
        #     deltedentry = course.query.filter(course.course_id==course_id).delete()
        #     details = request.get_json()
        #     if "course_name" not in details.keys():
        #         raise BError(status_code=400, errorcode="COURSE001", errormsg="Course Name is required and should be string")
        #     if "course_code" not in details.keys():
        #         raise BError(status_code=400, errorcode="COURSE002", errormsg="Course Code is required and should be string.")
        #     if details["course_name"] in (None,"") or type(details["course_name"]) != str:
        #         raise BError(status_code=400, errorcode="COURSE001", errormsg="Course Name is required and should be string")
        #     if details["course_code"] in (None,"") or type(details["course_code"]) != str:
        #         raise BError(status_code=400, errorcode="COURSE002", errormsg="Course Code is required and should be string.")
        #     if "course_description" not in details.keys():
        #         raise BError(status_code=400, errorcode="COURSE003", errormsg="Course Description should be string.")
        #     if type(details["course_description"]) != str:
        #         raise BError(status_code=400, errorcode="COURSE003", errormsg="Course Description should be string.")
        #     newentry = course(course_id=int(course_id), course_name=details["course_name"], course_code = details["course_code"], course_description = details["course_description"])
        #     db.session.add(newentry)
        #     db.session.commit()
        #     details["course_id"] = course_id
        #     return Success(status_code = 200, msg = details)
        # else:
        #     raise DefaultError(status_code=404)

    # def delete(self, course_id): pass
        # try:
        #     oldentry = course.query.filter(course.course_id==course_id).first()
        # except:
        #     raise DefaultError(status_code=500)
        # if oldentry:
        #     deltedentry = course.query.filter(course.course_id==course_id).delete()
        #     db.session.commit()
        #     raise DefaultError(status_code=200)
        # else:
        #     raise DefaultError(status_code=404)

    # @marshal_with(courseget)
    # def post(self):pass
#         details = request.get_json()
#         if "course_name" not in details.keys():
#             raise BError(status_code=400, errorcode="COURSE001", errormsg="Course Name is required and should be string")
#         if "course_code" not in details.keys():
#             raise BError(status_code=400, errorcode="COURSE002", errormsg="Course Code is required and should be string.")
#         if details["course_name"] in (None,"") or type(details["course_name"]) != str:
#             raise BError(status_code=400, errorcode="COURSE001", errormsg="Course Name is required and should be string")
#         if details["course_code"] in (None,"") or type(details["course_code"]) != str:
#             raise BError(status_code=400, errorcode="COURSE002", errormsg="Course Code is required and should be string.")
#         if "course_description" not in details.keys():
#             raise BError(status_code=400, errorcode="COURSE003", errormsg="Course Description should be string.")
#         if type(details["course_description"]) != str:
#             raise BError(status_code=400, errorcode="COURSE003", errormsg="Course Description should be string.")

#         search = course.query.filter(course.course_code == details["course_code"]).first()
#         if search:
#             raise DefaultError(status_code=409)
#         else:
#             tracker_name = request.form.get('tname')
#             new_tracker = tracker(tracker_name = request.form.get('tname'), \
#                                 tracker_type = request.form.get('ttype'), \
#                                 tracker_settings = request.form.get('tsettings'))
        
#             db.session.add(new_tracker)
#             new_assignment = assignment()
#             db.session.commit()
#             raise Success(status_code=201, msg=details)


# studentinfo = {
#   "student_id": fields.Integer,
#   "first_name": fields.String,
#   "last_name": fields.String,
#   "roll_number": fields.String
# }

# class Student(Resource):
#     @marshal_with(studentinfo)
#     def get(self, student_id):
#         try:
#             student_info = student.query.filter(student.student_id == student_id).first()
#         except:
#             raise DefaultError(status_code=500)
#         if student_info:
#             return student_info
#         else:
#             raise DefaultError(status_code=404)
    
#     @marshal_with(studentinfo)
#     def put(self, student_id):
#         try:
#             oldentry = student.query.filter(student.student_id==student_id).first()
#         except:
#             raise DefaultError(status_code=500)
#         if oldentry:
#             deltedentry = student.query.filter(student.student_id==student_id).delete()
#             details = request.get_json()
#             if "roll_number" not in details.keys():
#                 raise BError(status_code=400, errorcode="STUDENT001", errormsg="Roll Number is required and should be string")
#             if "first_name" not in details.keys():
#                 raise BError(status_code=400, errorcode="STUDENT002", errormsg="First Name is required and should be string.")
#             if details["roll_number"] in (None,"") or type(details["roll_number"]) != str:
#                 raise BError(status_code=400, errorcode="STUDENT001", errormsg="Roll Number is required and should be string")
#             if details["first_name"] in (None,"") or type(details["first_name"]) != str:
#                 raise BError(status_code=400, errorcode="STUDENT002", errormsg="First Name is required and should be string.")
#             if "last_name" not in details.keys():
#                 raise BError(status_code=400, errorcode="STUDENT003", errormsg="Last Name should be string.")
#             if type(details["last_name"]) != str:
#                 raise BError(status_code=400, errorcode="STUDENT003", errormsg="Last Name should be string.")
#             newentry = student(student_id=int(student_id), roll_number=details["roll_number"], first_name = details["first_name"], last_name = details["last_name"])
#             db.session.add(newentry)
#             db.session.commit()
#             details["student_id"] = student_id
#             return details
#         else:
#             raise DefaultError(status_code=404)

#     def delete(self, student_id):
#         try:
#             oldentry = student.query.filter(student.student_id==student_id).first()
#         except:
#             raise DefaultError(status_code=500)
#         if oldentry:
#             deltedentry = student.query.filter(student.student_id==student_id).delete()
#             db.session.commit()
#             raise DefaultError(status_code=200)
#         else:
#             raise DefaultError(status_code=404)

#     @marshal_with(studentinfo)
#     def post(self):
#         details = request.get_json()
#         if "roll_number" not in details.keys():
#             raise BError(status_code=400, errorcode="STUDENT001", errormsg="Roll Number is required and should be string")
#         if "first_name" not in details.keys():
#             raise BError(status_code=400, errorcode="STUDENT002", errormsg="First Name is required and should be string.")
#         if details["roll_number"] in (None,"") or type(details["roll_number"]) != str:
#             raise BError(status_code=400, errorcode="STUDENT001", errormsg="Roll Number is required and should be string")
#         if details["first_name"] in (None,"") or type(details["first_name"]) != str:
#             raise BError(status_code=400, errorcode="STUDENT002", errormsg="First Name is required and should be string.")
#         if "last_name" not in details.keys():
#             raise BError(status_code=400, errorcode="STUDENT003", errormsg="Last Name should be string.")
#         if type(details["last_name"]) != str:
#             raise BError(status_code=400, errorcode="STUDENT003", errormsg="Last Name should be string.")

#         search = student.query.filter(student.roll_number == details["roll_number"]).first()
#         if search:
#             raise DefaultError(status_code=409)
#         else:
#             newentry = student(roll_number=details["roll_number"], first_name = details["first_name"], last_name = details["last_name"])
#             db.session.add(newentry)
#             db.session.commit()
#             entry = student.query.filter(student.roll_number == details["roll_number"]).first()
#             details['student_id'] = entry.student_id
#             raise Success(status_code=201, msg=details)



# class Enrollment(Resource):
#     def get(self,student_id):
#         try:
#             srow =  student.query.filter(student.student_id == student_id).first()
#         except:
#             raise DefaultError(status_code=500)
#         if srow:
#             enrows = enrollments.query.filter(enrollments.estudent_id == student_id).all()
#             if enrows:
#                 enroll_list = []
#                 for i in range(len(enrows)):
#                     enrow = enrows[i]
#                     enroll = {"enrollment_id":enrow.enrollment_id, "student_id":enrow.estudent_id, "course_id":enrow.ecourse_id}
#                     enroll_list.append(enroll)
#                 return enroll_list
#             else:
#                 raise DefaultError(status_code=404)
#         else:
#             raise BError(status_code=400, errorcode="ENROLLMENT002", errormsg="Student does not exist.")

#     def post(self,student_id):
#         details = request.get_json()
#         if "course_id" not in details.keys():
#             raise BError(status_code=400, errorcode="ENROLLMENT003", errormsg="Course code is required and should be string")
#         if details['course_id'] is None or type(details['course_id']) != int:
#             raise BError(status_code=400, errorcode="ENROLLMENT003", errormsg="Course code is required and should be string")
#         course_id = details['course_id']
#         try:
#             search = student.query.filter(student.student_id == student_id).first()
#             csearch = course.query.filter(course.course_id == course_id).first()
#         except:
#             raise DefaultError(status_code=500)
#         if csearch:
#             if search:
#                 enrols = enrollments.query.filter(enrollments.estudent_id == student_id).filter(enrollments.ecourse_id == course_id).first()
#                 if enrols:
#                     a = self.get(student_id=student_id)
#                     if a:
#                         raise Success(status_code=201, msg=json.dumps(a,indent=2))
#                 newenroll = enrollments(estudent_id = student_id, ecourse_id = course_id)
#                 db.session.add(newenroll)
#                 db.session.commit()
#                 a = self.get(student_id=student_id)
#                 if a:
#                     raise Success(status_code=201, msg=json.dumps(a,indent=2))
#             else:
#                 raise DefaultError(status_code=404)
#         else:
#             raise BError(status_code=400, errorcode="ENROLLMENT001", errormsg="Course does not exist")

#     def delete(self,student_id, course_id):
#         try:
#             search = student.query.filter(student.student_id == student_id).first()
#             enrolsearch = enrollments.query.filter(enrollments.estudent_id == student_id).filter(enrollments.ecourse_id == course_id).first()
#             csearch = course.query.filter(course.course_id == course_id).first()
#         except:
#             raise DefaultError(status_code=500)
#         if csearch:
#             if search:
#                 if enrolsearch:
#                     delenrolls = enrollments.query.filter(enrollments.estudent_id == student_id).filter(enrollments.ecourse_id == course_id).delete()
#                     db.session.commit()
#                     raise DefaultError(status_code=200)
#                 else:
#                     raise DefaultError(status_code=404)
#             else:
#                 raise BError(status_code=400, errorcode="ENROLLMENT002", errormsg="Student does not exist")
#         else:
#             raise BError(status_code=400, errorcode="ENROLLMENT001", errormsg="Course does not exist")


