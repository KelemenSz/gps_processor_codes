import numpy
import scipy as sci
import scipy.special as sp
from numpy import *
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm, colors
from itertools import chain
import pymap3d as pm
import os
from vpython import vector, rotate
import pylab as pl
import math

s_o_l = 1.0 #3.0*10**8


def getSTARS_for_galactic_system(path):
	# D = normvec(pd.read_csv(path+'/star_d_positions.csv',skiprows=0).values)	
	# S = normvec(pd.read_csv(path+'/star_s_positions.csv',skiprows=0).values)
	D = normvec(pd.read_csv(path+'/Denebola_positions.csv',skiprows=0).values)	
	S = normvec(pd.read_csv(path+'/Sadalmelik_positions.csv',skiprows=0).values)

	sun = pd.read_csv(path+'/SUN_positions.csv',skiprows=0).values
	galactic_n_p = pd.read_csv(path+'/GNP_positions.csv',skiprows=0).values
	galactic_center = pd.read_csv(path+'/GC_positions.csv',skiprows=0).values

	# star_1 = pd.read_csv(path+'/star_Mirphak_positions.csv',skiprows=0).values	
	# star_2 = pd.read_csv(path+'/star_Vega_positions.csv',skiprows=0).values

	# nunki = pd.read_csv(path+'/star_Nunki_positions.csv',skiprows=0).values
	# capella = pd.read_csv(path+'/star_Capella_positions.csv',skiprows=0).values
	nunki = pd.read_csv(path+'/Nunki_positions.csv',skiprows=0).values
	capella = pd.read_csv(path+'/Capella_positions.csv',skiprows=0).values
	return sun, galactic_n_p, galactic_center, nunki, capella, S, D

def get_mean_direction_over_time(systems, directions):
	# systems = systems.T
	# print(systems)
	l = min(len(directions), len(systems[0]))
	phi = 0.
	theta = 0.
	# print('lenght', l)
	for i in range(l):
		out = cartesian_to_galactic(array([systems[0][i], systems[1][i], systems[2][i]]), directions[i])
		# print('out:', out)
		theta += out[0]
		phi += out[1]
	return theta/float(l), phi/float(l)


def normvec(vec):
	a = empty(shape(vec))
	for i in range(len(vec)):
		a[i] = unit(vec[i])
	return a


def scal(v1, v2):
	return vdot(array(v1), array(v2))


def unit(v):
	return 1/sqrt(scal(v,v))*array(v)


def group_results(results_dict, l):
	groupped = []
	group = []
	n = len(list(results_dict.keys()))
	l_groups = int(n/l)
	i = 0
	if l_groups > 1:
		for k, v in results_dict.items():
			if i >= l_groups:
				groupped.append(list(chain(*group)))
				group = []
				group.append(v)
				i = 0
				continue
			group.append(v)
			i += 1
	# print("groupped: ", groupped, len(group))
	return groupped


def parse_sats_data(sat_data_file):
	data = {}
	epoch = []
	with open(sat_data_file) as in_file:
		lineList = [line.rstrip('\n').split(",") for line in in_file]
		# n=10000
		for line in lineList[1:]:
			if line[0][0] == "E":
				data[line[-1]] = epoch
				epoch = []
				continue
			epoch.append([float(line[0]), float(line[1]), float(line[2]), float(line[3])])
	return data


def dr_lenght(v1, v2):
	return sqrt((v1[0]-v2[0])**2 + (v1[1]-v2[1])**2 + (v1[2]-v2[2])**2)


def get_comon(vA, vB):
	data = []
	for a in vA:
		# print(a)
		for b in vB:
			if dr_lenght(a[:3], b[:3]) < 500:
				# print(dr_lenght(a[:3], b[:3]))
				data.append([a, b])
	return data

def prepare_data(path):
	user_ = pd.read_csv(path+'/user_pos_allsatellites.csv',skiprows=1).values#.transpose()	
	user_mean = mean(user_, axis=0).astype('float64')
	sat_data = parse_sats_data(os.path.join(path, "all_sats_pos_time.csv"))
	return user_mean, sat_data


def extract_common_sats(satA, satB):
	comon_parts = {}
	for kA, vA in satA.items():
		vB = satB.get(kA, None)
		if vB:
			comon = get_comon(vA, vB)
			comon_parts[kA] = comon
	return comon_parts


def calc_for_one_sattelite(posA, posB, sat_pr_both):
	S_A = sat_pr_both[0][:3]
	S_B = sat_pr_both[1][:3]
	t1 = sat_pr_both[0][3]/s_o_l
	t2 = sat_pr_both[1][3]/s_o_l
	AS = dr_lenght(S_A, posA)
	BS = dr_lenght(S_B, posB)
	# print("Sat distances: ", AS/1000.0, BS/1000.0)
	# print(S_A)
	return unit((array(posA) + array(posB))/2.0 - array(S_A)), get_proportion_v0(AS, t1, BS, t2)


def calc_for_one_sattelite_beta(posA, posB, sat_pr_both):
	S_A = sat_pr_both[0][:3]
	S_B = sat_pr_both[1][:3]
	t1 = sat_pr_both[0][3]/s_o_l
	t2 = sat_pr_both[1][3]/s_o_l
	AS = dr_lenght(S_A, posA)
	BS = dr_lenght(S_B, posB)
	# print("Sat distances: ", AS/1000.0, BS/1000.0)
	# print(S_A)
	A_SA_i = unit(array(posA) - array(S_A))
	B_SB_j = unit(array(posB) - array(S_B))
	n = A_SA_i - B_SB_j
	# print(dr_lenght(array([0,0,0]), n))
	return unit(n), get_proportion_v1(AS, t1, BS, t2) #* dr_lenght(array([0,0,0]), n)


def  get_proportion_v0(AS, t1, BS, t2):
	# print(AS*t2/BS/t1)
	# print(AS,t2,BS,t1)
	return float(AS)*float(t2)/float(BS)/float(t1)

def  get_proportion_v1(AS, t1, BS, t2):
	# print(AS*t2/BS/t1)
	# print(AS,t2,BS,t1)
	r = float(AS)*float(t2)/float(BS)/float(t1)
	return r * (r - 1)**2

# ===============================================================================================================================================================================

def process_one_epoch(posA, posB, data_from_common_sats):
	dirrection_value = []
	for sats in data_from_common_sats:
		# dirrection_value.append(calc_for_one_sattelite(posA, posB, sats))
		dirrection_value.append(calc_for_one_sattelite_beta(posA, posB, sats))

	return dirrection_value

# ===============================================================================================================================================================================

def process_all(posA, posB, common_data):
	raw_results = {}
	for k, v in common_data.items(): # k = epoch index
		raw_results[k] = process_one_epoch(posA, posB, v)
	return raw_results

def raw_results_to_GCS(results_ECEF, GCS):
	results_GCS = []
	for i in range(len(results_ECEF)):
		results_group = results_ECEF[i]
		GCS_group = GCS[i]
		results_group_GCS = []
		for direction, value in results_group:
			results_group_GCS.append([ecef_to_gcs(GCS_group, direction), value])
		results_GCS.append(results_group_GCS)
	return results_GCS


def transform_matrix(f1, f2):  # transforms from f1 to f2
	R = array([
		[dot(f2[0], f1[0]), dot(f2[0], f1[1]), dot(f2[0], f1[2])],
		[dot(f2[1], f1[0]), dot(f2[1], f1[1]), dot(f2[1], f1[2])],
		[dot(f2[2], f1[0]), dot(f2[2], f1[1]), dot(f2[2], f1[2])]
		])
	return R


def get_theta_phi(v):
	if 0.99 < v[0] and 1.01 > v[0] and -0.01 < v[1] and 0.01 > v[1] and -0.01 < v[2] and 0.01 > v[2]:
		return 0.0, 0.0
	if 0.99 < v[1] and 1.01 > v[1] and -0.01 < v[0] and 0.01 > v[0] and -0.01 < v[2] and 0.01 > v[2]:
		return 90.0, 0.0
	if 0.99 < v[2] and 1.01 > v[2] and -0.01 < v[1] and 0.01 > v[1] and -0.01 < v[0] and 0.01 > v[0]:
		return 0.0, 90.0
	return None, None


def ecef_to_gcs(system, vector):
	vector = unit(vector)
	system = normvec(system)
	ECEF = array(([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]))
	R = transform_matrix(ECEF, system)
	return around(R.dot(vector), decimals = 3)


def cartesian_to_galactic(system, vector):
	vector = unit(vector)
	system = normvec(system)
	ECEF = array(([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]))
	R = transform_matrix(ECEF, system)
	vector_in_system = around(R.dot(vector), decimals = 3)
	# print(vector_in_system)
	theta, phi = get_theta_phi(vector_in_system)
	if not theta and not phi:
		phi, theta, _ = pm.ecef2geodetic(vector_in_system[0], vector_in_system[1], vector_in_system[2])
		# print(theta, phi)
		phi = 90 - degrees(arccos(scal(ECEF[2], vector_in_system)))
	return theta, phi
	# return degrees(theta), degrees(phi)


def cartesian_to_spherical(vector):
	theta, phi = get_theta_phi(vector)
	ECEF = array(([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]))
	if not theta and not phi:
		phi, theta, _ = pm.ecef2geodetic(vector[0], vector[1], vector[2])
		# print(theta, phi)
		phi = 90 - degrees(arccos(scal(ECEF[2], vector)))
	return radians(theta), radians(phi)

# =================================================================================================
# =================================================================================================

def get_global_stars(star_dir, directory):
	star_dirs = [f.path for f in os.scandir(star_dir) if f.is_dir()]
	for stardir in star_dirs:
		if directory[-8:] == stardir[-8:]:
			return get_stars_for_CMBR_cmap(stardir)
			

def get_stars_for_CMBR_cmap(path):
	sun, galactic_n_p, galactic_center, nunki, galactic_anti_center, S, D = getSTARS_for_galactic_system(path)

	sun = normvec(sun)
	galactic_n_p = normvec(galactic_n_p)
	galactic_center = normvec(galactic_center)
	galactic_anti_center = normvec(galactic_anti_center)
	nunki = normvec(nunki)
	Nx = normvec(galactic_center).astype('float64')
	Nz = normvec(galactic_n_p).astype('float64')
	Ny = -get_third_dir_by_cross_product(Nz, Nx)

	return Nx, Ny, Nz, S, D


def get_third_dir_by_cross_product(A, B):
	l = min(len(A), len(B))
	C = empty((l, 3))
	for i in range(l):
		C[i] = cross(A[i], B[i])
	return normvec(C)

def get_raw_results(pathA, pathB):
	posA, dataA = prepare_data(pathA)
	posB, dataB = prepare_data(pathB)
	comonAB = extract_common_sats(dataA, dataB)
	# print(comonAB)
	raw_results = process_all(posA, posB, comonAB)
	# print(len(list(raw_results.keys())))
	# raw_results = list(chain(*raw_results.values())) 
	# print(raw_results)
	return raw_results


def process_raw_GCS_data(raw_results_GCS, resolution):
	theta_max = math.pi
	phi_max = math.pi/2.0
	rot_theta = arange( -theta_max, theta_max, resolution)
	rot_phi = arange( -phi_max, phi_max, resolution)
	cmap_v = zeros((len(rot_theta), len(rot_phi)))
	cmap_count = zeros((len(rot_theta), len(rot_phi)))
	for direction, value in raw_results_GCS:
		i, j = get_ij_on_map(direction, resolution)
		# print(i, j)
		cmap_v[i][j] += value
		cmap_count[i][j] += 1
	return divide(cmap_v, cmap_count), cmap_count


def get_ij_on_map(direction, resolution):
	theta_max = math.pi
	phi_max = math.pi/2.0
	rot_theta = arange( -theta_max, theta_max, resolution)
	rot_phi = arange( -phi_max, phi_max, resolution)
	theta, phi = cartesian_to_spherical(direction)

	I_f = 0
	J_f = 0
	l_theta = int(len(rot_theta)/2.0)
	l_phi = int(len(rot_phi)/2.0)
	for i in range(-l_theta, l_theta):
		if i*resolution > theta:
			I_f = i + l_theta
			break
	for i in range(-l_phi, l_phi):
		if i*resolution > phi:
			J_f = i + l_phi
			break
	# print(theta, phi, "   ", I_f, J_f)
	return I_f, J_f



def plot_mollweid(matrix, star_directions, root_directory, name, resolution, anot=True):
	child_dirname = os.path.split(root_directory)[-1]+'_24h'
	plt.clf()
	try:
		cmap_save = pd.DataFrame(matrix)
		cmap_save.to_csv(os.path.join(root_directory, 'data_GS_'+child_dirname + "_" + name + "_" + resolution + '.csv'), index=True)
		print('Matrix.csv saved!')
	except:
		pass
	ra = linspace(-math.pi, math.pi, len(matrix))
	dec= linspace(-math.pi/2, math.pi/2, len(matrix[0]))

	X,Y = meshgrid(ra, dec)
	Z = matrix.T
	plt.figure()
	ax = pl.subplot(111)#, projection = 'mollweide')
	fig = ax.contourf(X,Y,Z,100)
	# fig = ax.imshow(rot90(fliplr(matrix), -1))
	if anot:
		for k, v in star_directions.items():
			add_star_annotated(v[0], v[1], k, ax)

	# ax.set_title('---$(24h)$', fontsize=15)  # , fontweight='bold')
	plt.xlabel(r'$\theta$',fontsize=15)#Italic font method
	plt.ylabel(r'$\phi$',fontsize=15)#Bold font method without fontweight parameters
	pl.colorbar(fig)
	ax.grid()
	# ax.contour(X,Y,Z,10,colors='k')
	# pl.show()
	fig_name1 = os.path.join(root_directory, 'data_GS_'+child_dirname + "_" + name + "_" + resolution + '.png')
	pl.savefig(fig_name1, bbox_inches='tight')


def add_star_annotated(theta, phi, name, ax):
	# print(S[0],S[1])
	# print(D[0],D[1])
	# y = radians(array([S[1], D[1]]))
	# x = radians(array([S[0], D[0]]))
	# print(x, y)
	theta = radians(theta)
	phi = radians(phi)
	ax.text(theta, phi, name, fontsize=12)
	ax.scatter(theta,phi, marker='x',c='k',s=15)
	# print(theta, phi)
	# ax.annotate(name,
 #            xy=array(theta, phi),
 #            xycoords='data')
	# ,
            
 #            arrowprops=
 #                dict(facecolor='black', shrink=0.05),
 #                horizontalalignment='left',
 #                verticalalignment='top')



def process_one_day(pathA, pathB, star_dir, resolution, root=None, fill_out=1.0): # fill_out=0.0 in case when the "r * (r-1)^2" values are in the data matrix
	# print(os.path.isdir(star_dir), pathB)
	Nx, Ny, Nz, S, D = get_global_stars(star_dir, os.path.dirname(pathB))
	l = len(Nx)
	star_directions_in_GCS = {}
	star_directions_in_GCS['GNP'] = get_mean_direction_over_time(array([Nx, Ny, Nz]), Nz)
	star_directions_in_GCS['GC'] = get_mean_direction_over_time(array([Nx, Ny, Nz]), Nx)
	star_directions_in_GCS['OY of GCS'] = get_mean_direction_over_time(array([Nx, Ny, Nz]), Ny)
	star_directions_in_GCS['Sadalmelic'] = get_mean_direction_over_time(array([Nx, Ny, Nz]), S)
	star_directions_in_GCS['Denebola'] = get_mean_direction_over_time(array([Nx, Ny, Nz]), D)
	# =================================================================================================================
	GCS_all = [array([Nx[i], Ny[i], Nz[i]]) for i in range(l)]
	raw_results_ECEF = get_raw_results(pathA, pathB)
	# print(list(raw_results_ECEF.values())[:100])
	groupped_raw_results_ECEF = group_results(raw_results_ECEF, l)
	# print(groupped_raw_results_ECEF[50][:5])
	

	groupped_raw_results_GCS = raw_results_to_GCS(groupped_raw_results_ECEF, GCS_all)

	raw_results_GCS = list(chain(*groupped_raw_results_GCS))#[::10000]
	print("Raw results in GCS are in: (data size)", len(raw_results_GCS))
	# print(raw_results_GCS[:100][1])
	mean_data, count = process_raw_GCS_data(raw_results_GCS, resolution)
	mean_data = nan_to_num(mean_data, nan=fill_out)
	# print(mean_data)
	# print(count)
	if root is None:
		root = os.path.dirname(os.path.dirname(pathA))
	plot_mollweid(count, star_directions_in_GCS, root, "histogram", str(int(degrees(resolution))), anot=True)
	plot_mollweid(mean_data, star_directions_in_GCS, root, "cmap", str(int(degrees(resolution))), anot=True)


def is_all_data(path, needed_files, add_allsatellites=False):
	if add_allsatellites:
		path = os.path.join(path, "allsatellites")
	try:

		list_files_with_paths = [f.path for f in os.scandir(path) if f.is_file()]
		
		count = 0
		for needed in needed_files:
			for file in list_files_with_paths:
				if os.path.basename(file) == needed:
					count += 1
					if count == len(needed_files):
						return True
	except:
		pass
	return False


def get_same_days_folders(root, needed_files):
	list_subfolders_with_paths = [f.path for f in os.scandir(root) if f.is_dir()]
	for folderA in list_subfolders_with_paths:
		folderA = os.path.join(folderA, "allsatellites")
		if not is_all_data(folderA, needed_files):
			continue
		for folderB in list_subfolders_with_paths:
			folderB = os.path.join(folderB, "allsatellites")
			if not is_all_data(folderB, needed_files):
				continue
			print(os.path.basename(os.path.dirname(folderA))[:4], os.path.basename(os.path.dirname(folderB))[:4])
			if os.path.basename(os.path.dirname(folderA))[-8:] == os.path.basename(os.path.dirname(folderB))[-8:] and os.path.basename(os.path.dirname(folderA))[:4] != os.path.basename(os.path.dirname(folderB))[:4]:
				return folderA, folderB
	return None, None


def process_one_day_from_root(path, needed_files, star_dir, resolution):
	folderA, folderB = get_same_days_folders(path, needed_files)
	
	if folderA:
		print("\n\n Data will be processed in: ", path, "\n\n")
		process_one_day(folderA, folderB, star_dir, resolution)
		return True
	print("\n\n Data not found in: ", path, "\n\n")
	return False


def process_many_days_from_root(root_directory, needed_files, star_dir, resolution):
	list_subfolders_with_paths = [f.path for f in os.scandir(root_directory) if f.is_dir()]
	for day_path in list_subfolders_with_paths:
		process_one_day_from_root(day_path, needed_files, star_dir, resolution)


def find_corresponding_dirs_in_different_roots(root_A, root_B, day=False):
	dir_pairs = []
	A_subfolders_with_paths = [f.path for f in os.scandir(root_A) if f.is_dir()]
	B_subfolders_with_paths = [f.path for f in os.scandir(root_B) if f.is_dir()]
	if not day:
		for A_dir in A_subfolders_with_paths:
			A_dirname = os.path.split(A_dir)[-1]
			for B_dir in B_subfolders_with_paths:
				B_dirname = os.path.split(B_dir)[-1]
				if A_dirname == B_dirname or A_dirname[-6:] == B_dirname[-6:]:
					dir_pairs.append([A_dir, B_dir])
		return dir_pairs


def create_dir(root_path, dir_name):
	results_dir = os.path.join(root_path, dir_name)
	if not os.path.isdir(results_dir):
		os.makedirs(results_dir)
	return results_dir


def find_same_days_and_process(path_A, path_B, result_path, needed_files, star_dir, resolution):
	d = 0
	if os.path.isdir(path_A) and os.path.isdir(path_B) and os.path.isdir(result_path):
		month_pairs = find_corresponding_dirs_in_different_roots(path_A, path_B)
		for A_month, B_month in month_pairs:
			month_name = os.path.split(A_month)[-1]
			print(month_name)
			# condition = True  # month_name in ["augusztus", "november"]
			# if condition:
			# print("---------------------------------------------------")
			# print(month_name)

			day_pairs = find_corresponding_dirs_in_different_roots(A_month, B_month)
			for A_day, B_day in day_pairs:
				date = str(os.path.split(B_day)[-1])[-8:]
				
				if is_all_data(A_day, needed_files, True) and is_all_data(B_day, needed_files, True):
					result_month = create_dir(result_path, month_name)
					result_day = create_dir(result_month, date)
					
					# print(A_day, B_day)
					# print("---------------------------------------------------")

					print("\n\n Data will be processed from: ", A_day, "    ", B_day, "\n", "Index of the process: ", d, "\n")
					# print("Day B: ", B_day)
					A_day = os.path.join(A_day, "allsatellites")
					B_day = os.path.join(B_day, "allsatellites")

					process_one_day(A_day, B_day, star_dir, resolution, root=result_day, fill_out=0.0)
					d += 1
				else:
					print("\n Data not found for: ", date, "\n")

	print(d)



# =================================================================================================
# =================================================================================================


star_dir = r"/Users/kelemensz/Documents/Research/GPS/STARS_GREENWICH/STARS_2020"
resolution = radians(5.0)
needed_files = ["user_pos_allsatellites.csv", "all_sats_pos_time.csv"]
# process_one_day(sat_data_fileA, sat_data_fileB, star_dir, resolution)

mounth_path = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/to_process/a"
# process_many_days_from_root(mounth_path, needed_files, star_dir, resolution)


day_path = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/test/20200803"


# process_one_day_from_root(day_path, needed_files, star_dir, resolution)

place_A = r"/Users/kelemensz/Documents/Research/GPS/process/global_GCS_axis/PERTH_daily_measurements"
place_B = r"/Users/kelemensz/Documents/Research/GPS/process/global_GCS_axis/process_NZLD"
# results_root = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/processed_data/automatic_processing"
results_root = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/processed_data/automatic_processing_no_weight"

# find_same_days_and_process(place_A, place_B, results_root, needed_files, star_dir, resolution)






# ==================================================================================================================================================================================================
# ==================================================================================================================================================================================================
# ==================================================================================================================================================================================================
# ==================================================================================================================================================================================================
from scipy.ndimage import rotate
def rotateAntiClockwise(array):
    return rotate(array, 90)

def rebin(arr, new_shape):
    shape = (new_shape[0], arr.shape[0] // new_shape[0],
             new_shape[1], arr.shape[1] // new_shape[1])
    return arr.reshape(shape).mean(-1).mean(1)


def get_matrix(path):
	# print('Path: ', path)
	M = pd.read_csv(path, skiprows=0).values[:,1:]#.transpose()[0]#.astype('float64')	
	return M


def get_csv_file(directory):
  csv_ext = ".csv"
  files = next(os.walk(directory))[2]
  # files = [f.path for f in os.scandir(directory) if f.is_file()]
  
  files_with_path = []
  for file in files:
  	if os.path.splitext(file)[1] == csv_ext:
  		files_with_path.append(os.path.abspath(os.path.join(directory, file)))
  # print(files_with_path)
  return files_with_path

def select_cmap_hist(file_list):
	hist = None
	cmap = None
	for file in file_list:
		if "histogram" in str(os.path.split(file)[-1]):
			hist = file
		if "cmap" in str(os.path.split(file)[-1]):
			cmap = file
	return cmap, hist



def plot_mollweid_simple(matrix):
	ra = linspace(-math.pi, math.pi, len(matrix))
	dec= linspace(-math.pi/2, math.pi/2, len(matrix[0]))

	X,Y = meshgrid(ra, dec)
	Z = matrix.T
	plt.figure()
	ax = pl.subplot(111)#, projection = 'mollweide')
	fig = ax.contourf(X,Y,Z,100)
	# fig = ax.imshow(rot90(fliplr(matrix), -1))

	plt.xlabel(r'$\theta$',fontsize=15)#Italic font method
	plt.ylabel(r'$\phi$',fontsize=15)#Bold font method without fontweight parameters
	pl.colorbar(fig)
	ax.grid()
	# ax.contour(X,Y,Z,10,colors='k')
	pl.show()
	

def plot_more(path):
	csv_s = get_csv_file(path)
	M = []
	for f in csv_s:
		a = get_matrix(f)
		# print(shape(a))
		M.append(a)
		

	mm = zeros(shape(M[0]))
	for m in M:
		mm += m
	M = mm/float(len(M))
	# M = mean(M, axis=0)

	plot_mollweid_simple(M)
	M = rotateAntiClockwise(M)
	a = 6
	b = a #* 2
	M = rebin(M, (int(len(M)/b), int(len(M[0])/a)))
	plt.imshow(M)
	plt.colorbar()
	plt.show()


# path = r"/Users/kelemensz/Documents/Research/GPS/process/24h/triangular_method/data_GS__24h_cmap.csv"
path = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/atlagolt"
path = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/test/20200803/data_GS_20200803_24h_histogram_5.csv"
path = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/test/20200803/data_GS_20200803_24h_cmap_5.csv"
# plot_more(path)

def read_matrix(path):
	M = rotateAntiClockwise(pd.read_csv(path).values)
	# M = M[M<0.2]
	M = M[:-1, :-1]
	nn = zeros(shape(M))
	# M = nn + M[M<0.2]
	M[M >0.1] = 0
	# M = log(M+1.0)
	# M = around(M, decimals=0)

	plt.imshow(M)
	plt.colorbar()
	plt.show()

# read_matrix(path)

f_h = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/test/20200803/data_GS_20200803_24h_histogram_5.csv"
f_d = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/test/20200803/data_GS_20200803_24h_cmap_5.csv"
# read_matrix(f_d, f_h)

def modify_matrix_by_cond(data, histogram):
	H = rotateAntiClockwise(pd.read_csv(histogram).values[:,1:])
	M = rotateAntiClockwise(pd.read_csv(data).values[:,1:])
	# ind_no_data = where(H == 0.0)[0] # argwhere(H == 0.0)
	ind_no_data = array(H < 1) 
	
	M[ind_no_data] = 0.0

	# M[M >0.1] = 0
	# M = log(M+1.0)
	# M = around(M, decimals=0)
	

	# plt.imshow(around(log(H+1), decimals=0))
	# plt.imshow(M)
	# plt.colorbar()
	# plt.show()
	return M, H


def plot_save_imshow(matrix, root_directory, name, resolution="5", logplot=False):
	child_dirname = os.path.split(root_directory)[-1] + "_" + name + '_24h' + "_" + resolution
	plt.clf()
	try:
		cmap_save = pd.DataFrame(matrix)
		cmap_save.to_csv(os.path.join(root_directory, child_dirname + '.csv'), index=True)
		print('Matrix.csv saved: ', name, "   ", os.path.split(root_directory)[-1])
	except:
		pass
	if logplot:
		matrix = around(log(matrix+1.0), decimals=0)
	# else:		
	# 	matrix = (matrix/(amax(matrix) * 1.1))**3.0
	plt.imshow(matrix)
	plt.colorbar()
	# plt.show()
	fig_name = os.path.join(root_directory, 'data_GS_'+child_dirname + '.png')
	plt.savefig(fig_name, bbox_inches='tight')
	plt.clf()


def plot_save_imshow_2_maps(matrix1, matrix2, root_directory, name, resolution="5", logplot=True):
	print('Matrix.csv saved: ', name, "   ", os.path.split(root_directory)[-1])
	child_dirname = os.path.split(root_directory)[-1] + "_" + name + '_24h' + "_" + resolution
	plt.clf()
	if logplot:
		matrix1 = around(log(matrix1+1.0), decimals=0)

	
	fig, (ax1, ax2) = plt.subplots(2, 1)
	fig.subplots_adjust(left=0.02, bottom=0.1, right=0.95, top=0.94, wspace=0.5, hspace=0.3)
	sp1 = ax1.imshow(matrix1)
	# print(root_directory, "\n", shape(matrix1))
	ax1.set_title("Histogram")
	sp2 = ax2.imshow(matrix2)
	ax2.set_title("r*(r-1)^2")
	fig.colorbar(sp1, ax=ax1)
	fig.colorbar(sp2, ax=ax2)
	# plt.show()
	fig_name = os.path.join(root_directory, child_dirname + '.png')
	fig.savefig(fig_name, bbox_inches='tight')
	plt.clf()

# =============================================================================================================================
# =============================================================================================================================
# =============================================================================================================================

def create_averaged_plots_from_root(root_0):
	mean_all_cmap = []
	mean_all_hist = []
	subfolders_with_paths_months = [f.path for f in os.scandir(root_0) if f.is_dir()]
	for month_root in subfolders_with_paths_months:
		days_with_paths = [f.path for f in os.scandir(month_root) if f.is_dir()]
		mean_month_cmap = []
		mean_month_hist = []
		try:
			for day_root in days_with_paths:
				csv_files = get_csv_file(day_root)
				cmap, hist = select_cmap_hist(csv_files)
				if (cmap and hist) and (os.path.isfile(cmap) and os.path.isfile(hist)):
					M, H = modify_matrix_by_cond(cmap, hist)
					mean_month_cmap.append(M)
					mean_month_hist.append(H)
			mean_month_cmap = mean(array(mean_month_cmap), axis=0)
			mean_month_hist = mean(array(mean_month_hist), axis=0)
			plot_save_imshow_2_maps(mean_month_hist, mean_month_cmap, month_root, os.path.split(month_root)[-1], resolution="5")
			# plot_save_imshow(mean_month_cmap, month_root, "mean_cmap")
			# plot_save_imshow(mean_month_hist, month_root, "mean_hist", logplot=True)
			mean_all_cmap.append(mean_month_cmap)
			mean_all_hist.append(mean_month_hist)
			# print(mean_month_cmap)
		except:
			pass
	mean_all_cmap = mean(array(mean_all_cmap), axis=0)
	mean_all_hist = mean(array(mean_all_hist), axis=0)
	# print(mean_all_cmap)
	plot_save_imshow_2_maps(mean_all_hist, mean_all_cmap, root_0, os.path.split(root_0)[-1], resolution="5")
	# plot_save_imshow(mean_all_cmap, root_0, "mean_cmap")
	# plot_save_imshow(mean_all_hist, root_0, "mean_hist", logplot=True)

root_of_matrices = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/processed_data/automatic_processing"
# root_of_matrices = r"/Users/kelemensz/Documents/Research/GPS/process/triangular_method/processed_data/automatic_processing_no_weight")
create_averaged_plots_from_root(root_of_matrices)



