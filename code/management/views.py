from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from datetime import timedelta, datetime
import MySQLdb, time, csv, os
from urllib.parse import unquote

# Create your views here.

def DBConnect():
    return MySQLdb.connect(user='Your DB username', db='yuhesa', passwd='Your DB password', host='Your DB host', port=3306)
    #Make your databse setting here

def SQLQuery(SQL, commit = None, parameter = None, lastInsertID = 0):
    db = DBConnect()
    cursor = db.cursor()
    res = None
    if parameter:
        cursor.execute(SQL, parameter)
    else:
        cursor.execute(SQL)
    if commit:
        db.commit()
        if lastInsertID:
            cursor.execute('SELECT LAST_INSERT_ID()')
            res = cursor.fetchall()
        db.close()
        return res
    else:
        res = cursor.fetchall()
        db.close()
        return res 

def index(request):
    return render(request, 'index.html')
	
def user_profile(request):
    if request.session['is_superuser']:
        position = 'Super User'
    else:
        position = 'Manager'
        
    SQL = 'SELECT id, first_name, last_name, phone_number '
    SQL += 'FROM auth_user '
    SQL += 'WHERE id =' + str(request.session['id'])
    res = SQLQuery(SQL)
    user = {'id':res[0][0], 'name':res[0][1]+' '+res[0][2], 'phone_number':res[0][3]}
    return render(request, 'management/user_profile.html',{'user':user,'position':position})

def user_list(request):
    SQL = 'SELECT id, username, first_name, last_name, is_superuser, phone_number '
    SQL +='FROM auth_user' 
    res = SQLQuery(SQL)

    users = []
    for re in res:
    	users.append(
            {'id':re[0],
            'username':re[1],
            'name':re[2]+' '+re[3],
            'is_superuser':re[4],
            'phone_number':re[5]
            })
    return render(request, 'management/user_list.html',{'users': users})

def user_add(request):
    if request.method == "POST":
        username = request.POST.get('username', '')
        password =  request.POST.get('password', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        #e_mail = 'mail@email.com'
        SQL = "INSERT INTO auth_user(username,password,first_name,last_name,phone_number) "
        SQL += "VALUES(%s, %s, %s, %s, %s)"
        SQLQuery(SQL,1,[username,password,first_name,last_name,phone_number])
        return redirect('/accounts/user_list')
    else:
       return render(request, 'management/user_add.html')

def user_edit(request,pk):
    if request.method == "POST":
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phone_number = request.POST.get('phone_number', '')
        SQL = 'UPDATE auth_user '
        SQL += 'SET first_name=%s, last_name=%s, phone_number=%s '
        SQL += 'WHERE id='+str(pk)
        SQLQuery(SQL,1,[first_name,last_name,phone_number])
        if request.session['is_superuser']:
            return redirect('/accounts/user_list') #render(request, 'management/user_list.html')
        else:
            return redirect('/accounts/user_profile')
        
    else:
        SQL = 'SELECT first_name, last_name, phone_number '
        SQL += 'FROM auth_user '
        SQL += 'WHERE id = '+str(pk)
        result = SQLQuery(SQL)
        user = {'id':pk,'first_name':result[0][0],'last_name':result[0][1],'phone_number':result[0][2]} 
        return render(request, 'management/user_edit.html', {'user': user})
    
def user_delete(request,pk):
    SQL = 'DELETE FROM auth_user '
    SQL += 'WHERE id = '+str(pk)
    SQLQuery(SQL,1)

    return redirect('user_list')
    
def user_search(request):
    if request.method == "GET":
        SQL = 'SELECT DISTINCT auth_user_id, username, first_name, last_name, is_superuser, phone_number '
        SQL +='FROM (SELECT auth_user.id as auth_user_id, management_cctv.id as management_cctv_id, username, first_name, last_name, is_superuser, phone_number '
        SQL +='FROM management_cctv RIGHT JOIN auth_user ON management_cctv.in_charge_user_id = auth_user.id) as u_c WHERE '#'WHERE u.id = c.in_charge_user_id '
        search_type = request.GET.get('search_type','')
        search_field = request.GET.get('search_field','')
        search_field = '%'+search_field+'%'
        if search_type == 'name':
            SQL += '(u_c.first_name LIKE %s OR u_c.last_name LIKE %s)'
            res = SQLQuery(SQL,0,[search_field,search_field])
        elif search_type =='in_charged_cctv': 
            SQL += 'u_c.management_cctv_id LIKE \"'+search_field+'\"'
            res = SQLQuery(SQL)
        else:
            SQL += 'u_c.'+search_type+' LIKE \"'+search_field+'\"'
            res = SQLQuery(SQL)
        users = []
        not_exist = 1
        for re in res:
            users.append(
                {'id':re[0],
                'username':re[1],
                'name':re[2]+' '+re[3],
                'is_superuser':re[4],
                'phone_number':re[5]
                })
        return render(request, 'management/user_list.html', {'users': users,'search_type':search_type,'search_field':search_field,'notexist':not_exist})
    return redirect('accounts/user_list')

def password_change(request):
    if request.method == "POST":
        current_password = request.POST.get('current_password', '')
        new_password1 = request.POST.get('new_password1', '')
        new_password2 = request.POST.get('new_password2', '')
        if new_password1 != new_password2:
            return render(request, 'management/user_passwordchange.html',{'alert2':1})
        SQL = 'SELECT password '
        SQL += 'FROM auth_user '
        SQL += 'WHERE id = '+str(request.session['id'])
        password = SQLQuery(SQL)[0][0]
        if password == current_password:
            SQL = 'UPDATE auth_user '
            SQL += 'SET password=%s '
            SQL += 'WHERE id='+str(request.session['id'])
            SQLQuery(SQL,1,[new_password1])
            return redirect('/accounts/profile') 
        else:
            return render(request, 'management/user_passwordchange.html',{'alert1':1})      
    return render(request, 'management/user_passwordchange.html')

@csrf_protect
def login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '')
        pw = request.POST.get('password', '')
        
        SQL = 'SELECT id, first_name, last_name, is_superuser, phone_number '
        SQL +='FROM auth_user '
        SQL +='WHERE username=%s AND password=%s'
        res = SQLQuery(SQL,0, [username, pw])

        if res:
            request.session['id'] = res[0][0]
            request.session['username'] = username
            request.session['is_authenticated']= 1
            request.session['is_superuser'] = res[0][3]
            
        return render(request, 'index.html')
        
def logout(request):
    if request.session['is_authenticated']:
        request.session['is_authenticated'] = 0
        request.session['is_superuser'] = 0
        del request.session['id']
        del request.session['username']
    return render(request, 'index.html')

@csrf_protect
def cctv_add(request):
    if request.method == 'POST':
        if request.POST.get('model_name','')!='':  # POST: process registration of cctv
            model_name = request.POST.get('model_name')
            install_date = request.POST.get('install_date')
            in_charge_user_id = request.POST.get('in_charge_user')

            SQL = 'INSERT INTO management_cctv(MODEL_NAME, INSTALL_DATE, IN_CHARGE_USER_ID) '
            SQL +='VALUES(%s, %s, %s)'
            SQLQuery(SQL, 1, [model_name, install_date, in_charge_user_id])
        else:
            fileCCTV = request.FILES['fileCCTV']
            FileSystemStorage(location=settings.MEDIA_ROOT+'/CCTV_Add/').save(fileCCTV.name, fileCCTV)
            readfile = open(settings.MEDIA_ROOT+'/CCTV_Add/'+fileCCTV.name,'r')
            reader = csv.reader(readfile, delimiter = ',')
            next(reader)
            for row in reader:
                SQL = 'INSERT INTO management_cctv(MODEL_NAME, INSTALL_DATE, IN_CHARGE_USER_ID) '
                SQL += 'VALUES(%s,%s,%s)'
                SQLQuery(SQL,1,[row[0], datetime.strptime(row[1], "%Y-%m-%d").date(), int(row[2])])
            readfile.close()
        return redirect('cctv_list')
    else: # GET: show register form
        SQL = 'SELECT username, id '
        SQL +='FROM auth_user '
        res = SQLQuery(SQL)
        
        users = []
        for re in res:
            users.append(
            {'username':re[0],
             'id': re[1]
            })
            
        return render(request, 'management/cctv_add.html', {'users':users})
  
def cctv_list(request):  
    if request.session['is_superuser']:
        SQL = 'SELECT DISTINCT c.id, c.model_name, c.install_date, u.username '
        SQL +='FROM management_cctv AS c, auth_user AS u '
        SQL +='WHERE u.id = c.in_charge_user_id '
        SQL +='ORDER BY c.id ASC'
    else:
        SQL = 'SELECT DISTINCT c.id, c.model_name, c.install_date, u.username '
        SQL +='FROM management_cctv AS c, auth_user AS u '
        SQL +='WHERE u.id = c.in_charge_user_id AND u.id =' + str(request.session['id']) + ' '
        SQL +='ORDER BY c. id ASC'
    res = SQLQuery(SQL)

    cctvs = []
    for re in res:
    	cctvs.append(
            {'id':re[0],
            'model_name':re[1],
            'install_date':str(re[2]),
            'in_charge_user':re[3]
            })
    
    return render(request, 'management/cctv_list.html', {'cctvs': cctvs})
    
def cctv_edit(request, pk):
    if request.method == "POST":
        model_name = request.POST.get('model_name', '')
        install_date = request.POST.get('install_date', '')
        in_charge_user_id = request.POST.get('in_charge_user', '')
        
        SQL = 'UPDATE management_cctv '
        SQL += 'SET model_name=%s, install_date=%s, in_charge_user_id=%s '
        SQL += 'WHERE id='+str(pk)
        SQLQuery(SQL, 1, [model_name, install_date, in_charge_user_id])
        
        return redirect('cctv_list')
    else:
        SQL = 'SELECT model_name, install_date, in_charge_user_id '
        SQL += 'FROM management_cctv '
        SQL += 'WHERE id = '+str(pk)
        res = SQLQuery(SQL)
        cctv = {'id':pk, 'model_name':res[0][0], 'install_date':res[0][1], 'in_charge_user_id':res[0][2]} 

        SQL = 'SELECT username, id '
        SQL +='FROM auth_user '
        res = SQLQuery(SQL)
        
        users = []
        for re in res:
            users.append(
            {'username':re[0],
             'id': re[1]
            })
 
        return render(request, 'management/cctv_edit.html', {'cctv': cctv, 'users': users})

def cctv_search(request):
    if request.method == "GET":
        SQL = 'SELECT c.id, c.model_name, c.install_date, u.username '
        SQL +='FROM management_cctv AS c, auth_user AS u '
        SQL +='WHERE u.id = c.in_charge_user_id '
        search_type = request.GET.get('search_type','')
        search_field = request.GET.get('search_field','')
        search_field = '%'+search_field+'%'
        
        if search_type == 'name':
            SQL += 'AND (u.first_name LIKE %s OR u.last_name LIKE %s)'
            res = SQLQuery(SQL,0,[search_field,search_field])
        else: 
            SQL += 'AND c.'+search_type+' LIKE \"'+search_field+'\"'
            res = SQLQuery(SQL)
            
        cctvs = []
        not_exist = 1
        for re in res:
            not_exist = 0
            cctvs.append(
                {'id':re[0],
                'model_name':re[1],
                'install_date':str(re[2]),
                'in_charge_user':re[3]
                })
                
        return render(request, 'management/cctv_list.html',{'cctvs': cctvs, 'search_type': search_type, 'search_field': search_field, 'notexist': not_exist})
    return redirect('/cctv_list')
    
def cctv_delete(request,pk):
    SQL = 'DELETE FROM management_cctv '
    SQL += 'WHERE id = '+str(pk)
    SQLQuery(SQL,1)
    return redirect('cctv_list')

@csrf_protect
def video_add(request):
    if request.method == 'POST': 
        cctv_id = request.POST['cctv_id']
        space_id = request.POST['space_id']
        start_time = datetime.strptime(request.POST['datetime'],"%Y-%m-%dT%H:%M")
        end_time = start_time + timedelta(hours=1)
        duration = (end_time-start_time).total_seconds()
        fileVideo = request.FILES['fileVideo']
        fileLog = request.FILES['fileLog']

        URLvideo = FileSystemStorage(base_url=settings.MEDIA_URL+'video/'+str(space_id)+'/').url(FileSystemStorage(location=settings.MEDIA_ROOT+'/video/'+str(space_id)+'/').save(fileVideo.name, fileVideo))
        URLlog = FileSystemStorage(base_url=settings.MEDIA_URL+'log/'+str(space_id)+'/').url(FileSystemStorage(location=settings.MEDIA_ROOT+'/log/'+str(space_id)+'/').save(fileLog.name, fileLog))   
        SQL = 'INSERT INTO management_video(video_file,log_file,cctv_id,space_id,start_time,end_time,duration) '
        SQL += 'VALUES(%s,%s,%s,%s,%s,%s,%s)'
        videoID = SQLQuery(SQL,1,[URLvideo, URLlog, cctv_id, space_id, start_time, end_time, duration],1)[0][0]
        with FileSystemStorage(location=settings.MEDIA_ROOT+'/log/'+str(space_id)+'/').open(fileLog.name, "rt") as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            next(reader)
            for row in reader:
                SQL = 'INSERT INTO management_metalog(video_id,object_id,x_position,y_position,timestamp,size,velocity,color) '
                SQL += 'VALUES(%s,%s,%s,%s,%s,%s,%s,%s)'
                SQLQuery(SQL,1,[videoID, int(row[1]), float(row[2]), float(row[3]), datetime.fromtimestamp(int(row[0])), row[4], row[5],row[6]])
        #fetch meta statistic info from metalog
        SQL = 'SELECT count(id), count(DISTINCT object_id), avg(velocity), avg(size), avg(color) '
        SQL += 'FROM management_metalog '
        SQL += 'WHERE video_id='+str(videoID)
        stat = SQLQuery(SQL)[0]
        #update meta statistic info to video
        SQL = 'UPDATE management_video '
        SQL += 'SET records_number=%s, obj_number=%s, avg_velocity=%s, avg_size=%s, avg_color=%s '
        SQL += 'WHERE id='+str(videoID)
        SQLQuery(SQL,1,[stat[0],stat[1],stat[2],stat[3],stat[4]])
        return redirect('/video_list')
    else:
        if request.session['is_superuser']:
            SQL1 = 'SELECT id '
            SQL1 +='FROM management_cctv '
            SQL1 +='ORDER BY id ASC'
            SQL2 = 'SELECT id '
            SQL2 +='FROM management_space '
            SQL2 +='ORDER BY id ASC'
        else:
            SQL1 = 'SELECT c.id '
            SQL1 +='FROM management_cctv AS c, auth_user as u '
            SQL1 +='WHERE u.id = c.in_charge_user_id AND u.id ='+str(request.session['id'])+' '
            SQL1 +='ORDER BY c.id ASC '
            SQL2 = 'SELECT s.id '
            SQL2 +='FROM management_space AS s, auth_user AS u, management_cctv AS c '
            SQL2 +='WHERE u.id = c.in_charge_user_id AND s.cctv_id = c.id AND u.id =' + str(request.session['id'])+' '
            SQL2 +='ORDER BY s.id ASC '
        res1 = SQLQuery(SQL1)
        res2 = SQLQuery(SQL2)
        cctvs = []
        for re in res1:
            cctvs.append({'id':re[0]})
        spaces = []
        for re in res2:
            spaces.append({'id':re[0]})
        return render(request, 'management/video_add.html',{'cctvs':cctvs, 'spaces':spaces} )
  
def video_list(request):
    SQL = 'SELECT id, video_file, log_file, cctv_id, space_id, records_number, obj_number, avg_velocity, avg_size, avg_color, start_time, end_time, duration '
    SQL +='FROM management_video' 
    res = SQLQuery(SQL)
    videos = []
    for re in res:
        videos.append(
            {'id':re[0],
            'video_file':re[1],
            'log_file':re[2], 
            'cctv_id':re[3], 
            'space_id':re[4], 
            'records_number':re[5], 'obj_number':re[6], 'avg_velocity':re[7], 'avg_size':re[8], 'avg_color':re[9], 'start_time':re[10], 'end_time':re[11], 'duration':time.strftime('%H:%M:%S', time.gmtime(int(re[12])))
            })
    return render(request, 'management/video_list.html', {'videos': videos})

def video_search(request):
    res = []
    if request.method == 'GET' and 'cctv_id' in request.GET:
        SQL = 'SELECT DISTINCT id, video_file, log_file, cctv_id, space_id, records_number, obj_number, avg_velocity, avg_size, avg_color, start_time, end_time, duration '
        SQL +='FROM management_video '
        cctv_id = request.GET.get('cctv_id','')
        if cctv_id != '':
            SQL += 'WHERE cctv_id ='+str(cctv_id)
            res = SQLQuery(SQL)
    if request.method == 'GET' and 'sequence_id' in request.GET:
        sequence_id = request.GET.get('sequence_id','')
        if sequence_id != '':      
            SQL = 'SELECT DISTINCT v.id, video_file, log_file, cctv_id, space_id, records_number, obj_number, avg_velocity, avg_size, avg_color, start_time, end_time, duration '
            SQL += 'FROM management_video as v, management_neighbor as n, management_sequence as s '
            SQL += 'WHERE (n.space_1_id = v.space_id or n.space_2_id = v.space_id) and (s.neighbor_1_id = n.id or s.neighbor_2_id = n.id) '
            SQL += 'AND s.id ='+str(sequence_id)
            res = SQLQuery(SQL)
    if request.method == 'GET' and ('address' in request.GET or 'building_name' in request.GET or 'floor' in request.GET or 'inroom_position' in request.GET):
        address = request.GET.get('address','')
        building_name = request.GET.get('building_name','')
        floor = request.GET.get('floor','')
        inroom_position = request.GET.get('inroom_position','')
        SQL = 'SELECT DISTINCT v.id, video_file, log_file, v.cctv_id, space_id, records_number, obj_number, avg_velocity, avg_size, avg_color, start_time, end_time, duration '
        SQL += 'FROM management_video as v, management_space as s '
        SQL += 'WHERE v.space_id = s.id AND '
        addAND = 0
        if address != '':
            SQL += ' s.address LIKE \"%'+address+'%\"'
            addAND = 1
        if building_name != '':
            if addAND == 1: SQL += ' AND '
            SQL += ' s.building_name LIKE \"%'+building_name+'%\"'
            addAND = 1
        if floor != '':
            if addAND == 1: SQL += ' AND '
            SQL += ' s.floor LIKE \"%'+floor+'%\"'
            addAND = 1
        if inroom_position != '':
            if addAND == 1: SQL += ' AND '
            SQL += ' s.inroom_position LIKE \"%'+inroom_position+'%\"'
        res = SQLQuery(SQL)  
    if request.method == 'GET' and 'start_time' in request.GET and 'end_time' in request.GET:
        start_time = datetime.strptime(request.GET['start_time'],"%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(request.GET['end_time'],"%Y-%m-%dT%H:%M")
        if start_time != '' and end_time != '':
            SQL = 'SELECT DISTINCT id, video_file, log_file, cctv_id, space_id, records_number, obj_number, avg_velocity, avg_size, avg_color, start_time, end_time, duration '
            SQL += 'FROM management_video '
            SQL += 'WHERE start_time >= %s AND end_time <= %s'
            res = SQLQuery(SQL,0,[start_time,end_time])         
    videos = []
    videoID = []
    #generate file
    writefile = open(settings.MEDIA_ROOT+'/statistic/statistic.csv', "w")
    writefile.write('VideoID,CCTVID,SpaceID,StartTime,EndTime,RecordsNumber,ObjectNumber,AverageVelocity,AverageSize,AverageColor,Duration\n')
    for re in res:
        writefile.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (re[0],re[3],re[4],re[5],re[6],re[7],re[8],re[9],re[10],re[11],re[12]))
        videoID.append(re[0])
        videos.append(
            {'id':re[0],
            'video_file':re[1],
            'log_file':re[2], 
            'cctv_id':re[3], 
            'space_id':re[4], 
            'records_number':re[5], 'obj_number':re[6], 'avg_velocity':re[7], 'avg_size':re[8], 'avg_color':re[9], 'start_time':re[10], 'end_time':re[11], 'duration':time.strftime('%H:%M:%S', time.gmtime(int(re[12])))
            })    
    if len(videoID) != 0: #statistic
        format_strings = ','.join(['%s'] * len(videoID))
        db = DBConnect()
        cursor = db.cursor()
        SQL = 'SELECT count(id), count(DISTINCT object_id), avg(velocity), avg(size), avg(color) '
        SQL += 'FROM management_metalog '
        cursor.execute(SQL+"WHERE video_id IN (%s)" % format_strings,tuple(videoID))
        re = cursor.fetchall()[0]
        db.close()
        stat = {'records_number':re[0], 'obj_number':re[1], 'avg_velocity':re[2], 'avg_size':re[3], 'avg_color':re[4],'statFile':'/media/statistic/statistic.csv'}
        writefile.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (' ',' ',' ',' ',' ',re[0],re[1],re[2],re[3],re[4],' '))
    writefile.close()
    
    search = 1 
    return render(request, 'management/video_list.html', {'videos': videos, 'search':1, 'stat':stat})

@csrf_protect
def video_delete(request):
    if request.method == 'POST' and 'start_time' in request.POST and 'end_time' in request.POST:
        start_time = datetime.strptime(request.POST['start_time'],"%Y-%m-%dT%H:%M")
        end_time = datetime.strptime(request.POST['end_time'],"%Y-%m-%dT%H:%M")
        if start_time != '' and end_time != '':
            SQL = 'SELECT DISTINCT id '
            SQL += 'FROM management_video '
            SQL += 'WHERE start_time >= %s AND end_time <= %s'
            res = SQLQuery(SQL,0,[start_time,end_time]) 

            for re in res:
                video_id = re[0] 
                SQL = 'DELETE FROM management_metalog '
                SQL += 'WHERE video_id=%s'
                SQLQuery(SQL,1,[video_id]) 

                SQL = 'DELETE FROM management_video '
                SQL += 'WHERE id=%s'
                SQLQuery(SQL,1,[video_id]) 
                
                space_id = re[3]
                os.remove(os.path.join(settings.BASE_DIR, 'management'+unquote(re[1]) ))
                os.remove(os.path.join(settings.BASE_DIR, 'management'+unquote(re[2]) ))
    return redirect('video_list')

@csrf_protect
def space_add(request):
    if request.method == 'POST': # POST: add new space
        id = request.POST.get('id')
        building_name = request.POST.get('building_name')
        address = request.POST.get('address')
        floor = request.POST.get('floor')
        inroom_position = request.POST.get('inroom_position')
        cctv_id = request.POST.get('cctv_id')

        SQL = 'INSERT INTO management_space(ID, BUILDING_NAME, ADDRESS, FLOOR, INROOM_POSITION, CCTV_ID) '
        SQL +='VALUES(%s, %s, %s, %s, %s, %s)'
        SQLQuery(SQL,1, [id, building_name, address, floor, inroom_position, cctv_id])

        return redirect('space_list')
    else: # GET: show register form
        if request.session['is_superuser']:
            SQL = 'SELECT id '
            SQL +='FROM management_cctv '
            SQL +='ORDER BY id ASC'
        else:
            SQL = 'SELECT c.id '
            SQL +='FROM management_cctv AS c, auth_user as u '
            SQL +='WHERE u.id = c.in_charge_user_id AND u.id ='+str(request.session['id'])+' '
            SQL +='ORDER BY c.id ASC '
        res = SQLQuery(SQL)
        
        cctvs = []
        for re in res:
            cctvs.append(
            {'id':re[0]
            })
            
        return render(request, 'management/space_add.html', {'cctvs':cctvs})

def space_list(request):
    if request.session['is_superuser']:
        SQL = 'SELECT s.id, s.cctv_id, s.building_name, s.address, s.floor, s.inroom_position, u.username '
        SQL +='FROM management_space AS s, auth_user AS u, management_cctv AS c '
        SQL +='WHERE u.id = c.in_charge_user_id AND s.cctv_id = c.id '
    else:
        SQL = 'SELECT s.id, s.cctv_id, s.building_name, s.address, s.floor, s.inroom_position, u.username '
        SQL +='FROM management_space AS s, auth_user AS u, management_cctv AS c '
        SQL +='WHERE u.id = c.in_charge_user_id AND s.cctv_id = c.id AND u.id =' + str(request.session['id'])
    res = SQLQuery(SQL)

    spaces = []
    for re in res:
    	spaces.append(
            {'id':re[0],
            'cctv_id':re[1],
            'building_name':re[2],
            'address':re[3],
            'floor':str(re[4]),
            'inroom_position':re[5],
            'in_charge_user':re[6],
            })
    
    return render(request, 'management/space_list.html', {'spaces': spaces})
				
def space_edit(request, pk):
    if request.method == "POST":
        building_name = request.POST.get('building_name')
        address = request.POST.get('address')
        floor = request.POST.get('floor')
        inroom_position = request.POST.get('inroom_position')
        SQL = 'UPDATE management_space '
        SQL += 'SET building_name=%s, address=%s, floor=%s, inroom_position=%s '
        SQL += 'WHERE id='+str(pk)
        SQLQuery(SQL, 1, [building_name, address, floor, inroom_position])
        return redirect('space_list')       

    else:
        SQL = 'SELECT building_name, address, floor, inroom_position '
        SQL += 'FROM management_space '
        SQL += 'WHERE id = '+str(pk)
        result = SQLQuery(SQL)
        space = {'id':pk, 'building_name':result[0][0], 'address':result[0][1], 'floor':result[0][2], 'inroom_position':result[0][3]} 
        return render(request, 'management/space_edit.html', {'space': space})

def space_delete(request,pk):
    SQL = 'DELETE FROM management_space '
    SQL += 'WHERE id = '+str(pk)
    SQLQuery(SQL,1)
    return redirect('space_list')

@csrf_protect
def neighbor_add(request):
    if request.method == 'POST': # POST: add new neighbor
        id = request.POST.get('id')
        space_1_id = request.POST.get('space_1')
        space_2_id = request.POST.get('space_2')
        route_name = request.POST.get('route_name')
        route_position = request.POST.get('route_position')
        if(space_1_id != space_2_id):
            SQL = 'INSERT INTO management_neighbor(ID, SPACE_1_ID, SPACE_2_ID, ROUTE_NAME, ROUTE_POSITION) '
            SQL +='VALUES(%s, %s, %s, %s, %s) '
            SQLQuery(SQL, 1, [id, space_1_id, space_2_id, route_name, route_position])

        return redirect("neighbor_list")
    else: # GET: show register form
        SQL = 'SELECT id, building_name '
        SQL +='FROM management_space '
        SQL +='ORDER BY id ASC'
        res = SQLQuery(SQL)
        
        spaces = []
        for re in res:
            spaces.append(
            {'id':re[0],
             'building_name':re[1]
            })
        return render(request, 'management/neighbor_add.html', {'spaces':spaces})
		
def neighbor_list(request):
    SQL = 'SELECT n.id, s1.building_name, s2.building_name, route_name, route_position '
    SQL +='FROM management_neighbor AS n '
    SQL +='JOIN management_space AS s1 ON n.space_1_id = s1.id '
    SQL +='JOIN management_space AS s2 ON n.space_2_id = s2.id '
    res = SQLQuery(SQL)

    neighbors = []
    for re in res:
    	neighbors.append(
            {'id':re[0],
            'space_1':re[1],
            'space_2':re[2],
            'route_name':re[3],
            'route_position':re[4]
            })
    return render(request, 'management/neighbor_list.html', {'neighbors': neighbors})

def neighbor_edit(request, pk):
    if request.method == "POST":
        space_1_id = request.POST.get('space_1')
        space_2_id = request.POST.get('space_2')
        route_name = request.POST.get('route_name')
        route_position = request.POST.get('route_position')
        if(space_1_id != space_2_id):
            SQL = 'UPDATE management_neighbor '
            SQL += 'SET space_1_id=%s, space_2_id=%s, route_name=%s, route_position=%s '
            SQL += 'WHERE id='+str(pk)
            SQLQuery(SQL, 1, [space_1_id, space_2_id, route_name, route_position])
        return redirect('neighbor_list')       

    else:
        SQL = 'SELECT space_1_id, space_2_id, route_name, route_position '
        SQL += 'FROM management_neighbor '
        SQL += 'WHERE id = '+str(pk)
        result = SQLQuery(SQL)
        neighbor = {'id':pk, 'space_1_id':result[0][0], 'space_2_id':result[0][1], 'route_name':result[0][2], 'route_position':result[0][3]} 

        SQL = 'SELECT id, building_name '
        SQL +='FROM management_space '
        res = SQLQuery(SQL)
        
        spaces = []
        for re in res:
            spaces.append(
            {'id':re[0],
             'building_name': re[1]
            })

        return render(request, 'management/neighbor_edit.html', {'neighbor': neighbor, 'spaces': spaces})
           
def neighbor_delete(request,pk):
    SQL = 'DELETE FROM management_neighbor '
    SQL += 'WHERE id = '+str(pk)
    SQLQuery(SQL,1)
    return redirect('neighbor_list')

@csrf_protect  
def sequence_add(request):
    if request.method == 'POST': # POST: add new sequence
        id = request.POST.get('id')
        neighbor_1_id = request.POST.get('neighbor_1')
        neighbor_2_id = request.POST.get('neighbor_2')
        
        SQL = 'SELECT s.building_name '
        SQL +='FROM management_neighbor AS n, management_space AS s '
        SQL +='WHERE n.id='+str(neighbor_1_id)+' AND n.space_2_id = s.id '
        s2_building_name = SQLQuery(SQL)[0][0]
        
        SQL = 'SELECT s.building_name '
        SQL +='FROM management_neighbor AS n, management_space AS s '
        SQL +='WHERE n.id='+str(neighbor_2_id)+' AND n.space_1_id = s.id '
        s1_building_name = SQLQuery(SQL)[0][0]   

        if ((neighbor_1_id != neighbor_2_id) & (s2_building_name == s1_building_name)):
            try:
                SQL = 'INSERT INTO management_sequence(ID, NEIGHBOR_1_ID, NEIGHBOR_2_ID) '
                SQL +='VALUES(%s, %s, %s) '
                SQLQuery(SQL, 1, [id, neighbor_1_id, neighbor_2_id])
            except MySQLdb.IntegrityError as e:
                SQL = 'SELECT n.id, s1.building_name, s2.building_name, route_name '
                SQL +='FROM management_neighbor AS n '
                SQL +='JOIN management_space AS s1 ON n.space_1_id = s1.id '
                SQL +='JOIN management_space AS s2 ON n.space_2_id = s2.id '
                res = SQLQuery(SQL)
                
                neighbors = []
                for re in res:
                    neighbors.append(
                    {'id':re[0],
                     's1_building_name':re[1],
                     's2_building_name':re[2],
                     'route_name':re[3]
                    })
                return render(request, 'management/sequence_add.html', {'neighbors':neighbors, 'error':str(e.__cause__)})
                
        return redirect("sequence_list")

    else: # GET: show register form
        SQL = 'SELECT n.id, s1.building_name, s2.building_name, route_name '
        SQL +='FROM management_neighbor AS n '
        SQL +='JOIN management_space AS s1 ON n.space_1_id = s1.id '
        SQL +='JOIN management_space AS s2 ON n.space_2_id = s2.id '
        res = SQLQuery(SQL)
        
        neighbors = []
        for re in res:
            neighbors.append(
            {'id':re[0],
             's1_building_name':re[1],
             's2_building_name':re[2],
             'route_name':re[3]
            })
        return render(request, 'management/sequence_add.html', {'neighbors':neighbors})
		
def sequence_list(request):
    SQL = 'SELECT s.id, n1.route_name, n2.route_name, n1s1.building_name, n1s2.building_name, n2s1.building_name, n2s2.building_name '
    SQL +='FROM management_sequence AS s '
    SQL +='JOIN management_neighbor AS n1 ON s.neighbor_1_id = n1.id '
    SQL +='JOIN management_neighbor AS n2 ON s.neighbor_2_id = n2.id '
    SQL +='JOIN management_space AS n1s1 ON n1.space_1_id = n1s1.id '
    SQL +='JOIN management_space AS n1s2 ON n1.space_2_id = n1s2.id '
    SQL +='JOIN management_space AS n2s1 ON n2.space_1_id = n2s1.id '
    SQL +='JOIN management_space AS n2s2 ON n2.space_2_id = n2s2.id '
    SQL +='ORDER BY s.id '
    res = SQLQuery(SQL)

    sequences = []
    for re in res:
    	sequences.append(
            {'id':re[0],
            'neighbor_1':re[1],
            'neighbor_2':re[2],
            'neighbor1_space1':re[3],
            'neighbor1_space2':re[4],
            'neighbor2_space1':re[5],
            'neighbor2_space2':re[6],
            })  
    return render(request, 'management/sequence_list.html', {'sequences': sequences})
           
def sequence_edit(request, pk):
    if request.method == "POST":
        neighbor_1_id = request.POST.get('neighbor_1')
        neighbor_2_id = request.POST.get('neighbor_2')
        
        SQL = 'SELECT s.building_name '
        SQL +='FROM management_neighbor AS n, management_space AS s '
        SQL +='WHERE n.id='+str(neighbor_1_id)+' AND n.space_2_id = s.id '
        s2_building_name = SQLQuery(SQL)[0][0]
        
        SQL = 'SELECT s.building_name '
        SQL +='FROM management_neighbor AS n, management_space AS s '
        SQL +='WHERE n.id='+str(neighbor_2_id)+' AND n.space_1_id = s.id '
        s1_building_name = SQLQuery(SQL)[0][0]
        
        if ((neighbor_1_id != neighbor_2_id) & (s2_building_name == s1_building_name)):
            try:
                SQL = 'UPDATE management_sequence '
                SQL += 'SET neighbor_1_id=%s, neighbor_2_id=%s '
                SQL += 'WHERE id='+str(pk)
                SQLQuery(SQL, 1, [neighbor_1_id, neighbor_2_id])
            except MySQLdb.IntegrityError as e:    
                SQL = 'SELECT neighbor_1_id, neighbor_2_id '
                SQL += 'FROM management_sequence '
                SQL += 'WHERE id = '+str(pk)
                result = SQLQuery(SQL)
                sequence = {'id':pk, 'neighbor_1_id':result[0][0], 'neighbor_2_id':result[0][1]} 
                
                SQL = 'SELECT n.id, s1.building_name, s2.building_name, route_name '
                SQL +='FROM management_neighbor AS n '
                SQL +='JOIN management_space AS s1 ON n.space_1_id = s1.id '
                SQL +='JOIN management_space AS s2 ON n.space_2_id = s2.id '
                res = SQLQuery(SQL)
                
                neighbors = []
                for re in res:
                    neighbors.append(
                    {'id':re[0],
                     's1_building_name':re[1],
                     's2_building_name':re[2],
                     'route_name':re[3]
                    })
                return render(request, 'management/sequence_edit.html', {'sequence': sequence, 'neighbors':neighbors, 'error':str(e.__cause__)})
                
        return redirect('sequence_list')       

    else:
        SQL = 'SELECT neighbor_1_id, neighbor_2_id '
        SQL += 'FROM management_sequence '
        SQL += 'WHERE id = '+str(pk)
        result = SQLQuery(SQL)
        sequence = {'id':pk, 'neighbor_1_id':result[0][0], 'neighbor_2_id':result[0][1]} 
        
        SQL = 'SELECT n.id, s1.building_name, s2.building_name, route_name '
        SQL +='FROM management_neighbor AS n '
        SQL +='JOIN management_space AS s1 ON n.space_1_id = s1.id '
        SQL +='JOIN management_space AS s2 ON n.space_2_id = s2.id '
        res = SQLQuery(SQL)
        
        neighbors = []
        for re in res:
            neighbors.append(
            {'id':re[0],
             's1_building_name':re[1],
             's2_building_name':re[2],
             'route_name':re[3]
            })
        return render(request, 'management/sequence_edit.html', {'sequence': sequence, 'neighbors':neighbors})

def sequence_delete(request,pk):
    SQL = 'DELETE FROM management_sequence '
    SQL += 'WHERE id = '+str(pk)
    SQLQuery(SQL,1)
    return redirect('sequence_list')
