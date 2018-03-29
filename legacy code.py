legacy code



########################################################

def JsonParser1(lista, ruta_output):		
	
	#La estructura de datos dificulta la extraccion de informacion segun sensor,
	#asumire que siempre va en la primera posicion la informacion del GPS en la lista
	#en la que se encuentra [0]

	print(ruta_output)

	data_locaciones = []
	#data_invalida = [] #Solo util para debug
	lineas_invalidas = 0
	for i in lista:
		if "sensors" in i.keys(): #Existen 2 formatos distintos 
			dic = i["sensors"][0]["data"]  
		else:
			dic = i["data"]  #Su longitud y latitud tienen una letra al final
		if dic["_RAW"] != "":
			#try:
			lon = convert_coordinates(dic["longitude"])  #Ocurre con valores vacios = ""
			lat = convert_coordinates(dic["latitude"]) #PENDIENTE: En formato 2 lon y lat terminan con letras que impiden conversion
			datatime = int(float(i["timestamp"]))
			data_locaciones.append((lat,lon,datatime))
			#except:
			#	lineas_invalidas+=1
			#	data_invalida.append(dic)
	print("Numero de lineas no parseadas: {}".format(lineas_invalidas))
	for i in data_invalida:
		print(i)


	#data_locaciones = [
	#(float(dic["longitude"]),
	#float(dic["latitude"]),
	#int(float(i["timestamp"])),
	#)for i in lista if dic["_RAW"] != ""] #lista de tuplas (latitude, longitude, timestamp)
	# El if se asegura de parsear data solo si es que existe

	kml = simplekml.Kml()
	for i in data_locaciones:
		pnt = kml.newpoint(name= time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(i[2])), coords=[(i[0],i[1])])  # lon, lat, optional height
		pnt.timestamp.when = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.localtime(i[2]))
	kml.save(ruta_output+"/"+"output.kml")


def runParser(ruta, filtro=""):  # Correr el script de forma masiva en una carpeta con archivos
	files = [f for f in listdir(ruta) if isfile(join(ruta, f))]
	contador = 0
	master_database=[] 
	for i in files:
		if i[-5:] == ".json" and filtro in i:  #Reconozco aquellos archivos que son .json
			with open(ruta+"/"+i, 'r') as database:
				print("Abri archivo {}".format(ruta+"/"+i))
				content = cleanJson(database) #Lista de diccionarios, cada diccionario es un log
				master_database += [json.loads(i) for i in content] #Lista de objetos JSON
				contador+=1
	JsonParser1(master_database,ruta)
	print("Numero de archivos .json transformados: {}".format(contador))



#runParser("/Users/benjamimo1/Documents/AgroBolt/Data-test") FUNCIONANDO para limpio, sucio
#INFO IDEAS
#Ejemplo de nombre: 2018-02-26 20/01/27.585904
#filtro es un string que intersecciono con el nombre de los archivos
#Crear kml unico para la salida de multiples files
#cleanJson("/Users/benjamimo1/Documents/AgroBolt/Drive/drive-download-20180322T181128Z-001/datafiles/DATA/2018-02-26 21:44:19.960523.json")
#runParser("/Users/benjamimo1/Documents/AgroBolt/Data-test")
#y = JsonData("/Users/benjamimo1/Documents/AgroBolt/Data-test/Formato\ 1\ -\ Limpio.json")