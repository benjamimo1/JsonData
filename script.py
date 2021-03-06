import json
import simplekml
import time
import sys
from os import listdir
from os.path import isfile, join, isdir
import csv
from math import radians, cos, sin, asin, sqrt


def haversine(lon1, lat1, lon2, lat2):  #Formula para calcular 
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    return km

def cleanJson(database):
	content = database.readlines()
	if "\x00" in (content[-1]):  #Busco byte asociado a informacion NULA, Chequeo solo la ultima linea
		content = content[:-1]
		print("Limpie el archivo")
	return content

def convert_coordinates(string):  #Transforma coordenadas con Orientacion al final a numero, probado con Formato 2- Limpio 2.json
	if isinstance(string, float):
		output = string
	else:
		output = string
		if string[-1].isalpha():
			if string[-1] in ["S","W"]:
				output = -float(string[:-1])/100
			else:
				output = float(string[:-1])/100

	return output

def check_valid_coordinate(string,option): #Avisar!, en el codigo matar
	if type(string) == str:
		if string[-1].isalpha():
			string = string[:-1]
		x = string.split(".")
		if option == "lon":
			y = 5
		elif option == "lat":
			y = 4
		else:
			print("No se declaro option")

		if len(x[0]) == y:
			if len(x[1]) == 7:
				return True
			else:
				print("Coordenada de largo correcto, precisión incorrecta")
				return False
		else:
			print("Coordenada de largo correcto incorrecto")  #No importa chequear precisión
			return False
	else:
		print("Pasa test por estar en formato numerico (parser)")
		return True


def remove_duplicates(x):  #Elimina duplicados de informacion (duplicados perfectos)
	return list(set(x))


class JsonData():
	def __init__(self):
		self.master_database= [] #lista de diccionarios

	@property
	def gps_database(self):
		output=[]
		for i in self.master_database:
			if "sensors" in i.keys():
				for sensor in i["sensors"]:
					if sensor["sensorType"] == "GPS6000":
						dic = sensor["data"]  #Aparentemente no siempre es el primero!
						dic["identifier"] = sensor["sensorID"]
			else:
				dic = i["data"]  #Su longitud y latitud tienen una letra al final:
				dic["identifier"] = i["sensorID"]


			if dic["_RAW"] != "" and dic["valid"] in ["1","2","3","4","5"]:
				dic["timestamp"]=i["timestamp"]
				output.append(dic)
		return output

	def export_to_kml(self,output_path):
		data_invalida = [] #Solo util para debug
		lineas_invalidas = 0
		data_locaciones = []
		for dic in self.gps_database:
			try:
				lon = convert_coordinates(dic["longitude"])
				lat = convert_coordinates(dic["latitude"])
				datatime = int(float(dic["timestamp"]))
				data_locaciones.append((lon,lat,datatime))
			except:
				lineas_invalidas+=1
				data_invalida.append(dic)

		#print(data_locaciones)
		print("Numero de lineas no parseadas: {}".format(lineas_invalidas))
		#for i in data_invalida:
		#	print(i)
		kml = simplekml.Kml()
		for i in data_locaciones:
			pnt = kml.newpoint(name= time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i[2])), coords=[(i[0],i[1])])  # lon, lat, optional height
			pnt.timestamp.when = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.localtime(i[2]))
		kml.save(output_path+"output.kml")

		print("Exporte archivo KML")

	def add_data(self,ruta,filtro=""):  #Agregar el filtro de limpieza de data aca fecha: 2018-02-03
		if (ruta[-5:] == ".json" or ruta[-4:] == ".log") and filtro in ruta:
			with open(ruta, 'r') as content:
				database = cleanJson(content) #Lista de diccionarios, cada diccionario es un log
				self.master_database += [json.loads(i) for i in database] #Lista de objetos JSON
				print("Importe el archivo {}".format(ruta))


		elif isdir(ruta):
			files = [f for f in listdir(ruta) if isfile(join(ruta, f))]
			contador = 0
			for i in files:
				if i[-5:] == ".json" and filtro in i:  #Reconozco aquellos archivos que son .json
					with open(ruta+"/"+i, 'r') as database:
						print("Abri archivo {}".format(ruta+"/"+i))
						content = cleanJson(database) #Lista de diccionarios, cada diccionario es un log
						self.master_database += [json.loads(i) for i in content] #Lista de objetos JSON
						contador+=1
			print("Numero de archivos .json importados: {}".format(contador))

		else:
			print("Error al importar")


	def clean_data(self):  #Export_Kml lo tiene incorporado, pero en caso de solo querer limpiar aca esta la funcion
		contador=0
		eliminados = []
		for i in self.master_database:
			if "sensors" in i.keys(): #Existen 2 formatos distintos 
				dic = i["sensors"][0]["data"]  
			else:
				dic = i["data"]  #Su longitud y latitud tienen una letra al final

			if dic["_RAW"] == "" or dic["valid"] not in ["1","2","3","4","5"]:  #Codigos asociados a data valida
				self.master_database.remove(i)
				contador+=1
				eliminados.append(i)

		#print(eliminados)
		print("Numero de entradas eliminadas: {}".format(contador))


	def export_to_csv(self,output_path,opcion):  #Para que funcione a de modificarse la estructura de datos a solo aquello que nos importa
		if opcion == "gps":
			data = self.gps_database

		keys = data[0].keys()
		with open(output_path, 'w') as output_file:
			dict_writer = csv.DictWriter(output_file, keys)
			dict_writer.writeheader()
			dict_writer.writerows(data)
		print("Exporte la data a csv")


	def filter_by_id(self,identifier):
		print("Filtre segun identifier: {}".format(identifier))
		return [i for i in self.gps_database if i["identifier"]==identifier]  

	def review(self,speed_limit, time_limit):
		output=[]
		redudant_data=[]
		disposable_data=[]
		duplicated = False

		for x, y in zip(self.gps_database[:-1], self.gps_database[1:]):

			latitude_2= convert_coordinates(y["latitude"])
			latitude_1= convert_coordinates(x["latitude"])
			longitude_2= convert_coordinates(y["longitude"])
			longitude_1= convert_coordinates(x["longitude"])

			delta_latitud = latitude_2 - latitude_1
			delta_longitude = longitude_2 - longitude_1
			delta_time = y["timestamp"]-x["timestamp"]

			distancia=(haversine(longitude_1,latitude_1,longitude_2,latitude_2))  
			velocidad= distancia/(delta_time/3600)

			if velocidad>speed_limit:  #Estoy usando timestamp
				print("Se alcanzo una velocidad anormal de {} en {}".format(velocidad,x["timestamp"]))

			if delta_time>time_limit:
				print("""Se encontró una laguna sin mediciones de {} segundos\nEsta se encontró entre ({},{})
""".format(delta_time,x["timestamp"],y["timestamp"]))

			if x["utc"] == y["utc"]:
				print("No se actualizó la data en {}, utc constante".format(x["timestamp"]))


			if (x["latitude"],x["longitude"]) == (y["latitude"],y["longitude"]) and x["utc"] != y["utc"]:
				duplicated = True
				redudant_data.append(y) #Considerar que deben quedar al menos 2
			else:
				if duplicated == True:
					duplicated = False
					redudant_data.pop()  #Teoricamente correcto

			if check_valid_coordinate(x["latitude"],"lat") and check_valid_coordinate(x["longitude"],"lon"):
				pass
			else:
				print("coordenada no cumple con formato valido: {}".format((x["latitude"],x["longitude"])))
				disposable_data.append(x)

		output = [i for i in self.gps_database if i not in redudant_data and i not in disposable_data]
		print("Numero de entradas redundantes: {}".format(len(redudant_data)))

		return output


if __name__ == '__main__':
	pass
	#Caso 1 exitoso, el check valid gps omite por que el formato no es verificable, presenta exceso velocidad
	#x = JsonData()
	#x.add_data("/Users/benjamimo1/Documents/AgroBolt/Data-test/Formato1-Limpio.json")
	#x.clean_data()
	##for i in x.gps_database:
	##	print(i)
	#x.export_to_csv("/Users/benjamimo1/Documents/AgroBolt/Data-test/output.csv","gps")
	#x.export_to_kml("/Users/benjamimo1/Documents/AgroBolt/Data-test")
	#x.review(40,10)
	#filtrado = x.filter_by_id("011")

	#Caso 2: Se revisa filtrado operativo a la hora de importar la data, presenta lagunas
	#x = JsonData()
	#x.add_data("/Users/benjamimo1/Documents/AgroBolt/sub_data/","2018-02-03")
	#x.clean_data()
	#x.export_to_csv("/Users/benjamimo1/Documents/AgroBolt/sub_data/2018-02-03.csv","gps")
	#x.export_to_kml("/Users/benjamimo1/Documents/AgroBolt/sub_data/")
	#y = x.review(40,10)
	#for i in y:
	#	print(y)

	#Caso 3: Archivo del tipo log
	x =  JsonData()
	x.add_data("/Users/benjamimo1/Documents/AgroBolt/GARCES_BACKUP_V2/data_2_datalogger-GARCES_01_2018-03-14 20_45_55.056404.log")
	for i in x.master_database:
		print(i)

	#toCSV = [{'name':'bob','age':25,'weight':200},
         #{'name':'jim','age':31,'weight':180}]
	#data_to_csv(toCSV,"/Users/benjamimo1/Documents/AgroBolt/Data-test/output.csv")



