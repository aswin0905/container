from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
from datetime import datetime,timedelta
import csv
import logging
import traceback

logging.basicConfig(filename='download.log',level=logging.INFO,format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')



#--------------------XML Data path----------------#
path = '/home/aswin/Documents/CCD/Data/All Patients CCDs Batch export-20240913-143827.530-UTC/'
#----------------Main HTML Path----------------#
html_doc = path+'Document List.html'

#------------Export Path---------------------#
exportpath = '/home/aswin/Documents/CCD/converted/'

#------------Patient LIST CSV Header----------------#
headerList = ['Patient ID','Patient First Name','Patient Last Name','Patient Middle Initial','Patient Age','Patient Date of Birth','Patient Race','Patient Ethnicity','Patient Gender','Patient Marital Status','Patient SSN','Patient MRN','Patient Account Number',' Patient Deceased',' Patient Language',' Patient Full Address',' Patient Zip Code',' Patient Phone Number','Patient Work Phone Number','Patient Cell Number','Patient Email','Patient Primary Pharmacy Name','Patient Status','Responsible Party Name','Responsible Party Full Address','Responsible Party Phone Number','Primary Service Location','Primary Service Location ID','Patient Fee Schedule Name','PCP']
with open(exportpath+'PatientList.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(headerList)
csvFile.close()

# #-----------------Patient ICD CSV Header-----------------#
headerICD = ['Encounter Date','ICD Code','Facility ID','Patient ID','Visit Type','Visit Status']
with open(exportpath+'PatientICD.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(headerICD)
csvFile.close()

# #-----------------Patient Vitals CSV Header-----------------#
headerVital = ["Encounter Date", "Appointment Provider Name", "Facility Name", "Patient Account Number", "Patient Age", "Patient DOB", "Patient Ethnicity", "Patient Name", "Patient Last Name", "Patient First Name", "Patient Middle Initial", "Patient Address", "Patient Address 2", "Patient City", "Patient State", "Patient Zipcode", "Patient Phone Number", "Patient e-Mail", "Patient Race", "Patient Sex", "Patient SSN", "Updated By", "Visit Status", "Visit Type", "Vital Default Value", "Vital Display Name", "Vital Name", "Vital Value", "Appointment Provider ID", "Encounter ID", "Facility ID", "Patient ID", "Vital ID"]
with open(exportpath+'Vital.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(headerVital)
csvFile.close()

#---------------------Patient CPT CSV Header--------------------#
headerCPT = ["Encounter Date", "CPT Code",	"CPT Code Description",	"Encounter Delete Flag", "Encounter Eligibility Status", "Encounter Type", "Encounter Type Description", "Facility ID", "Patient ID"]
with open(exportpath+'PatientCPT.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(headerCPT)
csvFile.close()

#---------------------Patient Lab CSV Header--------------------#
headerLab =  ["Lab Collection Date", "Lab Reviewed Date", "Lab Attribute", "Lab Attribute Value", "Lab Name", "Lab Result", "LOINC code", "Patient ID"]
with open(exportpath+'Labs.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(headerLab)
csvFile.close()

#---------------------Patient Medication CSV Header--------------------#
headerLab =  ["Appointment Date", "Start Date", "Stop Date", "Appointment Provider Name", "Average Whole Sale Price", "Average Whole Unit Price", "Dispense", "Duration","Encounter Lock","Encounter Type","Facility Name","Frequency","NDC Code","Patient Account Number","Patient Name","Prescription Name","Route","Rx Group Name","Strength","Take","Medication Count","Encounter ID","Facility ID","Patient ID","Rx Group ID"]
with open(exportpath+'Medication.csv', 'w') as csvFile:
    writer = csv.writer(csvFile)
    writer.writerow(headerLab)
csvFile.close()

soup = BeautifulSoup(open(html_doc), 'html.parser')
for link in soup.find_all('a'):
    filename = link.get('href')
    print(f"href value: {filename}") 
    if isfile(path+filename):
        print (filename)
    else:
        logging.info(filename)
        continue

    if(filename.endswith('.xml')):
        with open(path + filename, 'r') as xml_file:
            xml_soup = BeautifulSoup(xml_file, 'xml')
            # Find the title "Encounters"
            title_element = xml_soup.find('title', text="Encounters")
            # print(title_element)
            process_file = False
            process_file = False
            if title_element:
                tables = title_element.find_next('text').find_all('table')
                for table in tables:
                    for row in table.find_all('td'):
                        for inner_row in row:
                            if 'Dr Rosa Diaz Torres' in inner_row.get_text():
                                process_file = True
                                break
                        if process_file:
                            break
                    if process_file:
                        break

                  
            if process_file:
                #----------HTML Scraping ACC Num & Status -----------#
                accountnum = link.find_all_next()[4].text
                status = link.find_all_next()[5].text
                patient_fullname=link.find_all_next()[2].text
                print (accountnum)

                #-------------Patient Details fetch  from XML starts here -------------#
                patient = BeautifulSoup(open(path+filename).read(),"xml") #opens XML File
                firstName = patient.find('name').find_next()
                middleName = firstName.find_next()
                if middleName.name == "family":
                    middleName = ''
                else:
                    middleName = middleName.text
                firstName = firstName.text
                lastName = patient.find('family').text
                try:
                    date =  patient.find('birthTime')['value']
                except KeyError:
                    logging.info(KeyError)
                    continue
                dob = datetime.strptime(date, '%Y%m%d')
                age  = (datetime.today() - dob).days/365
                dob =  datetime.strftime(dob, '%Y-%m-%d')
                ethnicity = patient.find('ethnicGroupCode')
                entry_eth = dict(ethnicity.attrs)
                if not 'displayName'  in entry_eth.keys():
                    ethnicity = ethnicity['nullFlavor']
                    if ethnicity == 'NASK':
                        ethnicity = "Not Asked"
                    elif ethnicity =="ASKU":
                        ethnicity = "Asked, But not known"
                else:
                    ethnicity = ethnicity['displayName']
                race = patient.find('raceCode')   
                entry_race = dict(race.attrs)
                if not 'displayName'  in entry_race.keys():
                    race = race['nullFlavor']
                    if race == 'NASK':
                        race = "Not Asked"
                    elif race =="ASKU":
                        race = "Asked, But not known"
                else:
                    race = race['displayName']
                try:
                    gender = patient.find('administrativeGenderCode')['displayName']
                except KeyError:
                    gender = 'not specified'
                maritalStatus = patient.find('maritalStatusCode')
                if maritalStatus == 'None':
                    maritalStatus == ''
                patientDeceased = 'No'
                ssn = ' '
                mrn = ' '
                language = patient.find('languageCommunication').find_next()
                entry_lang = dict(language.attrs)
                if not 'code' in entry_lang.keys():
                    language = language['nullFlavor']
                    if language == 'NI':
                        language = "No Information"
                else:
                    language = language['code']
                address = patient.find('patientRole').find('addr')
                i=0
                street2 = ''
                street1 = ''
                for street in address.find_all('streetAddressLine'):
                    if i == 0:
                        street1 = street.text
                    if i == 1:
                        street2 = street.text
                    i = i+1
                city = address.find('city').text
                state = address.find('state').text
                country = address.find('country').text
                address = street1+" "+ street2+ " " +city+" "+state+" "+country
                patientzip = patient.find('postalCode').text
                phone1 = patient.find('patientRole').find_next('telecom')
                phone2 = phone1.find_next('telecom')
                phone3 = phone2.find_next('telecom')
                patientWorkPhone = " "
                patientHomePhone = " "
                patientMobilePhone = " "
                if phone1.parent.name == 'patientRole':
                    entry_phone = dict(phone1.attrs)
                    if not 'nullFlavor' in entry_phone.keys():
                        try:
                            phonetype = phone1['use']
                        except:
                            phonetype=""
                        if phonetype == 'WP':
                            patientWorkPhone = phone1['value'].split(':')[1]
                        if phonetype == 'HP':
                            patientHomePhone = phone1['value'].split(':')[1]
                        if phonetype == 'MC':
                            patientMobilePhone  = phone1['value'].split(':')[1]
                if phone2.parent.name == 'patientRole':
                    entry_phone = dict(phone2.attrs)
                    if not 'nullFlavor' in entry_phone.keys():
                        try:
                            phonetype = phone2['use']
                        except:
                            phonetype=""
                        if phonetype == 'WP':
                            patientWorkPhone = phone2['value'].split(':')[1]
                        if phonetype == 'HP':
                            patientHomePhone = phone2['value'].split(':')[1]
                        if phonetype == 'MC':
                            patientMobilePhone  = phone2['value'].split(':')[1]
                if phone3.parent.name == 'patientRole':
                    entry_phone = dict(phone3.attrs)
                    if not 'nullFlavor' in entry_phone.keys():
                        try:
                            phonetype = phone3['use']
                        except:
                            phonetype=""
                        if phonetype == 'WP':
                            patientWorkPhone = phone3['value'].split(':')[1]
                        if phonetype == 'HP':
                            patientHomePhone = phone3['value'].split(':')[1]
                        if phonetype == 'MC':
                            patientMobilePhone  = phone3['value'].split(':')[1]
                email = '' 
                responsible = ''
                responsiblePhone = ''
                responsibleName =  ''
                responsibleAddress = ''
                primaryPharmacy = ' '
                primaryLocation = 65
                primaryLocationID = 65
                feeSchedule = ''
                pcp_main=patient.find('documentationOf')
                try:
                    pcp=pcp_main.find('assignedPerson').find('name')
                    pcp=[i for i in pcp if i!=u'\n']
                    pcp_name=pcp.contents[1].text+" "+pcp.contents[2].text+" "+pcp.contents[3].text
                except:
                    pcp_name=""
                #--------write patient row to patient list -----#
                listRow = [accountnum,firstName,lastName,middleName,age,dob,race,ethnicity,gender,maritalStatus,ssn,mrn,accountnum,patientDeceased,language,address,patientzip,patientHomePhone,patientWorkPhone,patientMobilePhone,email,primaryPharmacy,status,responsibleName,responsibleAddress,responsiblePhone,primaryLocation,primaryLocationID,feeSchedule,pcp_name]
                try:
                    with open(exportpath+'PatientList.csv', "a") as fp:
                        wr = csv.writer(fp)
                        wr.writerow(listRow)
                except:
                    continue
                #-------------write end ------------------------#

                #------Medication starts here---------------#
                try:
                    medications=patient.find('title', text="Medications").find_next_siblings('text')[0].find('tbody')
                    for medication in medications.find_all('tr'):
                        ndc_code=medication.contents[1].text.replace('RxNorm: ','')
                        try:
                            med_start_date=medication.contents[4].text
                            med_start_date=datetime.strptime(med_start_date, '%Y-%m-%d')
                            med_start_date=datetime.strftime(med_start_date, '%Y-%m-%d')
                        except:
                            med_start_date=""
                        try:
                            med_end_date=medication.contents[5].text
                            med_end_date=datetime.strptime(med_end_date, '%Y-%m-%d')
                            med_end_date=datetime.strftime(med_end_date, '%Y-%m-%d')
                        except:
                            med_end_date=""
                        dose=medication.contents[3].text
                        route=medication.contents[0].text
                        drug=medication.contents[2].text
                        frequency=medication.contents[6].text
                        #--------write medication row to medication list -----#
                        listRow = [med_start_date,med_start_date,med_end_date,pcp_name,"","","","","","","",frequency,ndc_code,accountnum,patient_fullname,drug,route,"",dose,"","","","",accountnum,""]
                        with open(exportpath+'Medication.csv', "a") as fp:
                            wr = csv.writer(fp)
                            wr.writerow(listRow)
                except:
                    print("No medication data")
                
                #------Medication ends here---------------#
                #-----------Problems -- Patient ICD starts here---------------#
                problem = patient.find('title', text="Problem List")
                icd = ''
                encounterdate = ''
                icdstatus = ''
                for prob in problem.find_next_siblings('entry'):
                    for icdcode in prob.find('value').find_all('translation'):
                        if icdcode['codeSystemName'] =='ICD10CM':
                            icd =  icdcode['code']
                            icdtime = prob.find('effectiveTime').find('low')
                            icdstatus = prob.find('statusCode')['code']
                            entry_icdtime = dict(icdtime.attrs)
                            if not 'nullFlavor' in entry_icdtime.keys():
                                # encounterdate = datetime.strptime(icdtime['value'], '%Y%m%d%H%M%S')
                                # encounterdate = datetime.strptime(icdtime['value'], '%Y%m%d')
                                #encounterdate = datetime.strftime(encounterdate, '%Y-%m-%d')
                                icdtime_value = icdtime['value']
                                # Remove the timezone part from the string
                                icdtime_value_without_timezone = icdtime_value.split('+')[0]
                                # Parse the date-time string
                                encounterdate = datetime.strptime(icdtime_value_without_timezone, '%Y%m%d%H%M%S')

                            #----------Patient ICD CSV Single Row write -------------------#
                            if icd != '':
                                icdRow = [encounterdate,icd,primaryLocation,accountnum,'',icdstatus]
                                with open(exportpath+'PatientICD.csv', "a") as fp:
                                    wr = csv.writer(fp)
                                    wr.writerow(icdRow)
                            #-------------------write ends --------------------------------#

                #----------------Patient Vital Details Start Here ------------------------#
                try:
                    vitals = patient.find('title', text="Vital Signs").find_all_next('entry')
                    print(vitals)
                    if vitals:
                        for vital in vitals:
                            organizer = vital.find('organizer')
                            if organizer:  # Ensure the organizer exists
                                for component in organizer.find_all('component'):
                                    encdate = datetime.strptime(component.find('effectiveTime')['value'], '%Y%m%d%H%M%S%z')
                                    formatted_date = encdate.strftime('%Y-%m-%d')
                                    vitalname = component.find('code')['displayName']

                                    try:
                                        vitalvalue = component.find('value')['value']
                                    except KeyError:
                                        vitalvalue = ''
                                    vitalcode = component.find('code')['code']
                                    # Write patient vital row to Vital.csv
                                    vitalRow = [encdate, '', '', accountnum, age, dob, ethnicity, firstName + " " + lastName,
                                                lastName, firstName, middleName, street1, street2, city, state,
                                                patientzip, patientMobilePhone, email, race, gender, ssn, '', '', '',
                                                vitalvalue, vitalname, vitalname, vitalvalue, '', '', '', accountnum, vitalcode]
                                    with open(exportpath + 'Vital.csv', "a") as fp:
                                        wr = csv.writer(fp)
                                        wr.writerow(vitalRow)
                except Exception as e:
                    print("No Vital data"+traceback.format_exc())
            
                #-------------------Patient Procedures (CPT) Starts here ----------------------#
                try:
                    patientcpt = patient.find('title', text = "Procedures")
                    for cpt in patientcpt.find_next_siblings('entry'):
                        if cpt.find('code')['codeSystemName'] == 'HCPCS':
                            cptcode = cpt.find('code')['code']
                            #cptdate = datetime.strptime(cpt.find('effectiveTime')['value'],'%Y%m%d%H%M%S')
                            cptdate = datetime.strptime(cpt.find('effectiveTime')['value'],'%Y%m%d')
                            cptdate =  datetime.strftime(cptdate, '%Y-%m-%d')
                            cptdes = cpt.find('code')['displayName']

                            #--------write patient CPT row to patientCPT.csv -----#
                            cptRow = [cptdate,cptcode,cptdes,'','','','',primaryLocationID,accountnum]
                            with open(exportpath+'PatientCPT.csv', "a") as fp:
                                wr = csv.writer(fp)
                                wr.writerow(cptRow)
                            #--------------------write end ------------------------#
                except:
                    print("No CPT data")
                #----------------------Patient Lab Details Start here---------------#
                result = patient.find('title',text="Results")
                for lab in result.find_next_siblings('entry'):
                    #try:
                        #labdate = datetime.strptime(lab.find('effectiveTime')['value'],'%Y%m%d%H%M%S')
                    #    labdate = datetime.strftime(labdate, '%Y-%m-%d')
                    #except KeyError:
                    #    continue
                    try:
                        lab_xml_date = lab.find('effectiveTime')['value']
                        date_str = lab_xml_date[:-5] + 'Z'
                        tz_offset = lab_xml_date[-5:]
                        tz_delta = timedelta(hours=int(tz_offset[:3]), minutes=int(tz_offset[3:]))
                        date_obj = datetime.strptime(date_str, '%Y%m%d%H%M%SZ')
                        date_obj += tz_delta
                        labdate = date_obj.date()
                    except ValueError:
                        lab_xml_date = lab.find('effectiveTime')['value']
                        labdate = datetime.strptime(lab_xml_date, '%Y%m%d')
                        labdate = datetime.strftime(labdate, '%Y-%m-%d')
                    except KeyError:
                        continue
                    try:
                        testname= lab.find('code')['displayName']
                    except KeyError:
                        continue
                    try:
                        testresult = lab.find('value')['value']
                    except KeyError:
                        testresult = ''
                    if lab.find('value')['xsi:type'] == 'ST':
                        testresult = lab.find('value').text
                    loinc = ''
                    try:
                        if lab.find('code')['codeSystemName'] == 'LOINC':
                            loinc = lab.find('code')['code']
                    except KeyError:
                        loinc = ''
                    #--------write patient Lab row to Labs.csv -----#
                    labRow = [labdate,labdate,testname,testresult,testname,testresult,loinc,accountnum]
                    with open(exportpath+'Labs.csv', "a") as fp:
                        wr = csv.writer(fp)
                        wr.writerow(labRow)
                    #--------------------write end ------------------------#

                
            else:
                logging.info(f"Skipping file (no match for Dr Rosa Diaz Torres): {filename}")


