# Read SDT Python Code Example

```python
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

class sdtread():
    #Reads the ASCII Header from the File
    def getsdtheader():
        fid.seek(0)
        sdtData = fid.read()
        startStr = "|^Data Set^|"
        #Find Header End
        hLength = sdtData.find(startStr.encode()) + len(startStr) + 1
        #Get Header as String
        hContent = sdtData[0:hLength].decode('ansi').strip()
        return hContent,hLength+1

    #Reads the binary data
    def readbinary(nelements, dt, elType = ''):       
        if elType.lower().__contains__('complex'):
            tempArr = np.fromfile(fid, dt, nelements*2)
            data_array = tempArr[0::2] + 1j*tempArr[1::2]
        else:
            data_array = np.fromfile(fid, dt, nelements)

        data_array.shape = (nelements, 1)
        return data_array

    #Parses the ASCII Header to a Dictionary
    def get_data_description(hContent):
        hDict = {}
        section = '' 
        for item in hContent: 
            itemInfo = item.strip().split(':')  
            if len(itemInfo) == 2:
                temp = itemInfo[0].strip()
                key = f'{section}_{temp}'.strip('_')
                hDict.update({key : itemInfo[1].strip()})
            elif len(itemInfo) == 1:
                if 'First Axis' in itemInfo[0]:
                    section = 'First Axis'
                elif 'Second Axis' in itemInfo[0]:
                    section = 'Second Axis'
                else:
                    section = itemInfo[0].replace('-','').replace('Data Axis',' ').replace('( )','').strip()
        
        #Get sdt version
        sdtversion = hDict.get('Version')[0:3]
        global hSubsetIndex
        if sdtversion == '5.4' or sdtversion == '5.0':
            hSubsetIndex = 0
        else:
            hSubsetIndex = 1

        return hDict
    
    #Format Lookup    
    def subsetformat(dataFormat):
        eltypeDict = {'FLOAT 32':np.float32,'DOUBLE 64':np.double,'INTEGER 16':np.int16,'INTEGER 12':np.int16,'UNSIGNED INTEGER 16':np.uint16,'BYTE 8':np.uint8,'CHAR 8':np.int8,'COMPLEX16 16':np.int16}
        elbitsDict = {'FLOAT 32':32,'DOUBLE 64':64,'INTEGER 16':16,'INTEGER 12':12,'UNSIGNED INTEGER 16':16,'COMPLEX16 16':16}

        elType = eltypeDict.get(dataFormat,np.int8)
        elbits = elbitsDict.get(dataFormat,8)
        return elType,elbits
    
    def prop(prop,subsetIndex = -1): 
        if subsetIndex != -1:
            propKey = f'Data Subset {subsetIndex}_{prop}'
        else:
            propKey = prop              
        propVal = dataDesc.get(propKey, None)
        return propVal   

    # Extract Axes Info from the Header
    def get_axes(axisName = '',index = -1):
        axInf = None
        axUnits = ''
        if ('Measurement Range' in axisName or 'Interpretation' in axisName) and index > -1:
            measRange = str(sdtread.prop(axisName,index-1)).split(' ')
            if len(measRange) == 3:
                axUnits = measRange[2]
            if len(measRange) >= 2:
                if index > -1:
                    undef = sdtread.prop('Undefined Element',index-1)
                else:
                    undef = None
                axInf = {'Start' : measRange[0],'Range' : measRange[1],'Undefined':undef,'Units':axUnits}
        elif 'Swept Axis' in axisName and index > -1:
            swept = str(sdtread.prop(axisName,index-1)).split(' ')
            if len(swept) == 4:
                axUnits = swept[3] 
            if len(swept) >= 3:
                axInf = {'Points':swept[0],'Start':swept[1],'Resolution':swept[2],'Units':axUnits}
        else:
            if index > -1:
                axisName += f' {index}'                
            points = sdtread.prop(f'{axisName}_Number of Sample Points')    
            if points is not None:
                start = str(sdtread.prop(f'{axisName}_Minimum Sample Position')).split(' ')
                res = str(sdtread.prop(f'{axisName}_Sample Resolution')).split (' ')
                if len(start) == 2:
                    axUnits = start[1]      
                if len(start) >= 1:
                    axInf = {'Points':points,'Start':start[0],'Resolution':res[0],'Units':axUnits}            
                
        return axInf  

    #
    def getdata():
        readlog = ''

        subsetCount = int(dataDesc.get('Number of Data Subsets'))

        axis1,axis2 = sdtread.get_axes('First Axis'),sdtread.get_axes('Second Axis')

        subsets = {}
        fid.seek(headerLength)

        for i in range(subsetCount):
            si = i + hSubsetIndex

            #dataFormat = dataDesc.get(formatStr)
            dFormat,dBits = sdtread.subsetformat(sdtread.prop('Element Representation',si))  
            subsetLabel = sdtread.prop('Subset Label',si) 
            if subsetLabel == None or subsetLabel == '':
                subsetLabel = f'Subset {i}'

            axes = [None,None,None]        
            sweptAxis = sdtread.get_axes('Swept Axis',si+1)
            axis3 = sdtread.get_axes(f'Data Subset {si}')   
            element = sdtread.get_axes('Measurement Range',si+1)
            element['Type'] = sdtread.prop('Element Representation',si)
            if element is None:
                element = sdtread.get_axes('Interpretation',si+1)

            if sweptAxis is not None: #Slice with Swept axis
                axes[0] = sweptAxis
                axes[1] = axis1
                if axis3 is not None and int(axis3['Points']) > 1:
                    axes[0] = axis1
                    axes[1] = sweptAxis
                    axes[2] = axis3
            elif axis1 is None and axis2 is None: # AScan or strip chart
                axes[2] = axis3 
            elif axis1 is not None and axis2 is None: #No Second Axis: BScan Slice
                axes[0] = axis3
                axes[1] = axis1
            elif axis3 is not None and int(axis3['Points']) == 1: #CScan
                axes[0] = axis2
                axes[1] = axis1
            else: #Wfm Data
                axes[0] = axis2
                axes[1] = axis1
                axes[2] = axis3     

            axis1Points,axis2Points,axis3Points = 1,1,1
            if axes[0] is not None:
                axis1Points= int(axes[0]['Points'])
            if axes[1] is not None:
                axis2Points= int(axes[1]['Points'])
            if axes[2] is not None:
                axis3Points = int(axes[2]['Points'])
            points2read = axis1Points * axis2Points * axis3Points
            data = sdtread.readbinary(points2read,dFormat,element['Type'])

            if axis1Points == 1:
                subset = data
            elif axis2Points == 1:
                subset = data    
            elif axis3Points > 1:            
                subset = data.reshape(axis1Points,axis2Points,axis3Points)          
            elif sweptAxis is not None:
                #subset = data.reshape(axis1Points,axis2Points)    
                subset = data.reshape(axis2Points,axis1Points)   
            else:
                subset = data.reshape(axis1Points,axis2Points)
        
            subsets[i] ={'Subset Name': subsetLabel,'Shape':subset.shape,'Axes':axes}          
            if element is not None:
                element['Size'] = subset.itemsize
                subsets[i]['Element'] = element    

            if element is not None and element['Undefined'] != 'None':
                subset = np.where(subset==np.int64(element['Undefined']), np.nan, subset)
            if element is not None:         
                scaling = float(element['Range'])/(2**int(dBits))
                if element['Type'] == 'CHAR 8':
                    if abs(float(element['Start'])*2) == float(element['Range']):
                        offset = 0
                    else:
                        offset = 127
                    subset = (offset + subset)*scaling            
                elif dFormat is not np.float32 and dFormat is not np.double:     
                    subset = subset*scaling

            subsets[i]['Data'] = subset

            readlog += f'{i}\tStart : {fid.tell()}\tFormat : {dFormat}\tShape : {subset.shape}\n'      
        return subsets,readlog

class utils():
  def FileExists(path):
    file = Path(path)
    return file.is_file()
  
#Plot Data
  def plotdata(data,subsetindex):
    #Replace undefined Before Plotting
    subset = data[subsetindex]['Data']
    element = data[subsetindex]['Element']
    if element is not None and element['Undefined'] != 'None':
        subset = np.where(subset==np.int64(element['Undefined']), np.nan, subset)  
    
    #Plot the second subset of the sample datafile
    dims = len(subset.shape)
    if dims == 2:
        plt.imshow(subset,interpolation = 'none',origin='lower')  
    elif dims == 3:
        plt.imshow(subset[0,:,:],interpolation = 'none',origin='lower')
    elif dims == 1 or dims == 0:
        plt.plot(subset)
    plt.show()
    return data

def OpenSdt(fPath):
    # Launch File Browser
    global fid,dataDesc,headerLength
    # Open Binary file
    if utils.FileExists(fPath) == False:
        return None,-1,'File path was invalid!'
    fid = open(fPath,'rb')
    #Read Header
    storageDescription,headerLength = sdtread.getsdtheader()
    dataDesc = sdtread.get_data_description(storageDescription.split('\n'))

    #Read Data into Numpy Array    
    subsets,readlog = sdtread.getdata()
    ver = sdtread.prop('Version')
    readlog += f'{fPath}\n'
    readlog += storageDescription
    return subsets,readlog
   
def main():
    print('Enter File Path : ')
    filePath = input().strip('\"')
    data,read_log = OpenSdt(filePath)
    print(f'{read_log}\n{data.items()}')
    utils.plotdata(data,0)
    
if __name__ == '__main__':
    main()

```