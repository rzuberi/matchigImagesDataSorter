from flask import Flask, render_template, Response, request, redirect
import numpy as np
import tifffile
import io
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import random
import mysql.connector


app = Flask(__name__)

#@app.route('/display')
#def display():
#    array = np.squeeze(tifffile.imread('C:\\Users\\rz200\\Documents\\development\\cmFlask\\images\\' + str(0) + '.tiff'))
#    image = Image.fromarray(array.astype('uint8'))
#    file_object = io.BytesIO()
#    image.save(file_object, 'PNG')
#    file_object.seek(0)#
#
#    return render_template('image_display.html',user_image=send_file(file_object, mimetype='image/PNG'))
#

#    <img src="data:image/jpeg;base64,{{ image }}", height="350", width="350"/>

@app.route('/display/results')
def display_results():
    mydb = mysql.connector.connect(
              host="cellmatching.mysql.pythonanywhere-services.com",
              user="cellmatching",
              database="cellmatching$default",
              password="HelloMyCell44"
            )
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM Matches")
    my_result = mycursor.fetchall()
    print(my_result)
    return render_template('results_display.html',data=my_result)

@app.route('/')
def index_start():
    return redirect("/display/"+str(random.randint(0,167)))

@app.route('/display')
def display_start():
    return redirect("/display/"+str(random.randint(0,167)))

@app.route('/display/<matchID>', methods=['POST', 'GET'])
def display(matchID):
    print(request.method)
    if request.method == 'POST':
        if request.form['submit_button'] == 'Yes':
            #call the matchID on SQL
            mydb = mysql.connector.connect(
              host="cellmatching.mysql.pythonanywhere-services.com",
              user="cellmatching",
              database="cellmatching$default",
              password="HelloMyCell44"
            )
            mycursor = mydb.cursor()
            #increment the "yes match" by 1
            sql = "UPDATE Matches SET correctCount = correctCount + 1 WHERE matchID = " + matchID
            mycursor.execute(sql)
            mydb.commit()

            return redirect("/display/"+str(random.randint(0,167)))
        elif request.form['submit_button'] == 'No':
           #call the matchID on SQL
            mydb = mysql.connector.connect(
              host="cellmatching.mysql.pythonanywhere-services.com",
              user="cellmatching",
              database="cellmatching$default",
              password="HelloMyCell44"
            )
            mycursor = mydb.cursor()
            #increment the "no match" by 1
            sql = "UPDATE Matches SET incorrectCount = incorrectCount + 1 WHERE matchID = " + matchID
            mycursor.execute(sql)
            mydb.commit()

            return redirect("/display/"+str(random.randint(0,167)))
        elif request.form['submit_button'] == 'Unsure':
            return redirect("/display/"+str(random.randint(0,167)))
        else:
            return render_template('image_display.html')

    elif request.method == 'GET':
        print('GET')
        print(matchID)

        return render_template('image_display.html',id=matchID)

@app.route('/plot/<id>.png')
def plot_png(id):
    fig = create_figure(id)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_figure(id):

    #getting mysql connections
    mydb = mysql.connector.connect(
      host="cellmatching.mysql.pythonanywhere-services.com",
      user="cellmatching",
      database="cellmatching$default",
      password="HelloMyCell44"
    )

    mycursor = mydb.cursor()

    #sql = "UPDATE Matches SET correctCount = correctCount + 1 WHERE matchID = 1"
    #mycursor.execute(sql)
    #mydb.commit()
    mycursor.execute("SELECT * FROM Matches WHERE matchID = " +str(id))
    my_result = mycursor.fetchall()[0] #in a list but there's only one result

    #call the matchID on SQL
        #get the first image index
    first_image_index = my_result[1]
        #get the second image index
    second_image_index = my_result[2]
        #get the first cell index
    first_cell_index = my_result[3]
        #get the second cell index
    second_cell_index = my_result[4]


    #make the image arrays
        #get from the images folder the image at image index1
    array_file_path_first_image = "/home/cellmatching/mysite/images/" + str(first_image_index) + ".tiff"
    array_first_image = np.squeeze(tifffile.imread(array_file_path_first_image))
        #get from the images folder the image at image index2
    array_file_path_second_image = "/home/cellmatching/mysite/images/" + str(second_image_index) + ".tiff"
    array_second_image = np.squeeze(tifffile.imread(array_file_path_second_image))

    #get the cell centers
    cell_centers_per_image_file_path = "/home/cellmatching/mysite/cell_centers/cell_centers.txt"
    with open(cell_centers_per_image_file_path) as f:
        content = f.read().splitlines()
    lst = []
    for line in content:
        lst.append(eval(line))
    cell_centers_per_image = lst[0]
        #from the first image centers, get the cell center at cell index1
    first_image_cell_center = cell_centers_per_image[first_image_index][first_cell_index]
        #from the second image centers, get the cell center at cell index2
    second_image_cell_center = cell_centers_per_image[second_image_index][second_cell_index]

    #get the cell crops
    pad_val = 20
        #pad image1 and image2
    array_first_image_padded = np.pad(array_first_image, pad_val, mode='constant')
    array_second_image_padded = np.pad(array_second_image, pad_val, mode='constant')
        #crop image1 and image2 at the cell centers
    first_image_x = first_image_cell_center[0]+pad_val
    first_image_y = first_image_cell_center[1]+pad_val
    array_first_image_cropped = array_first_image_padded[first_image_y-pad_val:first_image_y+pad_val,first_image_x-pad_val:first_image_x+pad_val]

    second_image_x = second_image_cell_center[0]+pad_val
    second_image_y = second_image_cell_center[1]+pad_val
    array_second_image_cropped = array_second_image_padded[second_image_y-pad_val:second_image_y+pad_val,second_image_x-pad_val:second_image_x+pad_val]
        #these crops will be the displays

    fig = Figure()

    fig.suptitle('matchID: ' + str(id))

    axis1 = fig.add_subplot(1, 2, 1)
    axis1.title.set_text('image index: ' + str(first_image_index) + '\n' 'cell index: ' + str(first_cell_index) + '\n' + 'cell coordinates: ' + str(first_image_cell_center))
    #array_file_path = "/home/cellmatching/mysite/images/0.tiff"
    #array = np.squeeze(tifffile.imread(array_file_path))
    axis1.imshow(array_first_image_cropped)
    axis1.tick_params(axis='both',which='both',bottom=False,top=False,left=False,labelleft=False,labelbottom=False)

    axis2 = fig.add_subplot(1, 2, 2)
    axis2.title.set_text('image index: ' + str(second_image_index) + '\n' 'cell index: ' + str(second_cell_index) + '\n' + 'cell coordinates: ' + str(second_image_cell_center))
    #array_file_path = "/home/cellmatching/mysite/images/0.tiff"
    #array = np.squeeze(tifffile.imread(array_file_path))
    axis2.imshow(array_second_image_cropped)
    axis2.tick_params(axis='both',which='both',bottom=False,top=False,left=False,labelleft=False,labelbottom=False)

    return fig

if __name__ == '__main__':
   display_results()
