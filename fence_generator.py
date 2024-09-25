import maya.cmds as cmds

class FenceUI(object):
    
    def __init__(self) -> None:
        self.window = 'Fence_UI'
        self.title = 'Fence Generator'
        self.size = (500,400)
        self.fg = FenceGenerator()
        
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window, window=True)
            
        self.window = cmds.window(self.window, title=self.title, widthHeight=self.size)
        
        cmds.columnLayout(adjustableColumn=True, columnAlign='center', columnOffset=['both', 30])
        cmds.text(label='')
        cmds.text(self.title)
        cmds.separator(height=20)
        
        self.setPostMeshBtn = cmds.button(label='Set Post Mesh', command=self.setPostMesh)
        self.postMeshText = cmds.text(label='', visible=False)
        cmds.text(label = '')
        self.setRailMeshBtn = cmds.button(label='Set Rail Mesh', command=self.setRailMesh)
        self.railMeshText = cmds.text(label='', visible=False)
        cmds.text(label = '')
        self.setCurveBtn = cmds.button(label='Set Curve', command=self.setCurve)
        self.curveText = cmds.text(label='', visible=False)
        cmds.separator(height = 20)
        self.fg.numPostsSlider = cmds.intSliderGrp(label='Number of posts:', min=0, max=100, value=0, field=True)
        self.fg.postDistanceSlider = cmds.floatSliderGrp(label='Distance between posts:', min=0, max=100, value=0, field=True)
        cmds.text(label = '')
        self.fg.numRailsSlider = cmds.intSliderGrp(label='Rails per segment:', min=0, max=100, value=0, field=True)
        cmds.separator(height=20)
        self.generateFenceBtn = cmds.button(label='Generate Fence', command=self.fg.generateFence)
        
        cmds.showWindow()

    def setCurve(self, *args):
        # selectedObjs = cmds.ls(selection=True, type='nurbsCurve')
        selectedObjs = cmds.ls(selection=True)
        shapeNodes = cmds.listRelatives(selectedObjs, shapes=True)
        curve = None
        if shapeNodes:
            for node in shapeNodes:
                if (cmds.nodeType(node)) == 'nurbsCurve':
                    curve = node
                    break
        if curve:
            self.fg.curve = curve
            curveText = "Curve set to " + str(curve)
            cmds.text(self.curveText, edit=True, label=curveText, visible=True)
        else:
            cmds.warning('Please select a curve')
            
                               

    def setPostMesh(self, *args):
        selectedObjs = cmds.ls(selection=True, type='transform')
        if selectedObjs:
            postMesh = selectedObjs[0]
            self.fg.postMesh = postMesh
            postMeshText = 'Post mesh set to ' + str (postMesh)
            cmds.text(self.postMeshText, edit=True, label=postMeshText, visible=True)
        else:
            cmds.warning('Please select a valid mesh')
        
    def setRailMesh(self, *args):
        selectedObjs = cmds.ls(selection=True, type='transform')
        if selectedObjs:
            railMesh = selectedObjs[0]
            self.fg.railMesh = railMesh
            railMeshText = 'Rail mesh set to ' + str (railMesh)
            cmds.text(self.railMeshText, edit=True, label=railMeshText, visible=True)
        else:
            cmds.warning('Please select a valid mesh')
        
        
        
class FenceGenerator(object):
    def __init__(self) -> None:
        self.postMesh = None
        self.railMesh = None
        self.curve = None
        self.numPosts = 3
        self.postDistance = 5
        self.numRails = 2
    
    def generateFence(self, *args):   
        cmds.select(clear = True)
        self.numPosts = int(cmds.textFieldGrp(self.numPostsSlider, query=True, text=True))
        self.postDistance = float(cmds.textFieldGrp(self.postDistanceSlider, query=True, text=True))
        self.numRails = int(cmds.textFieldGrp(self.numRailsSlider, query=True, text=True))
    
        # Create a group to contain the fence
        fenceGroup = cmds.group(empty=True, name='FenceGroup')
        postSize = self.getSize(self.postMesh)
        railSize = self.getSize(self.railMesh)
        
        cmds.select(self.postMesh, r=True)
        postPivot = cmds.getAttr('.rotatePivot')[0]
        cmds.select(self.railMesh, r=True)
        railPivot = cmds.getAttr('.rotatePivot')[0]
        
        curveLength = cmds.arclen(self.curve)
        print(curveLength)
        postSpacing = curveLength / (self.numPosts - 1)
        
        for i in range(self.numPosts):
            postDuplicate = cmds.duplicate(self.postMesh, name=f'post_{i}')[0]
            
            curveParam = i * postSpacing / curveLength
            point = cmds.pointOnCurve(self.curve, parameter=curveParam, position=True)
            tangent = cmds.pointOnCurve(self.curve, parameter=curveParam, tangent=True)
            
            # TODO for now moving along the X axis, later let the user choose
            # If transformations have been frozen,subtract from transform
            # postX = -postPivot[0] + i * self.postDistance
            postX = -postPivot[0] + point[0]
            postY = -postPivot[1] + point[1]
            postZ = -postPivot[2] + point[2]
            cmds.move(postX, postY, postZ, postDuplicate)
            tangentVector = [tangent[0], tangent[1], tangent[2]]
            
            locator = cmds.spaceLocator(name=f'aimLocator_{i}')[0]
            locatorX = point[0] + tangent[0]
            locatorY = point[1] + tangent[1]
            locatorZ = point[2] + tangent[2]
            cmds.move(locatorX, locatorY, locatorZ, locator)
            cmds.aimConstraint(locator, postDuplicate, aimVector=[1, 0, 0], upVector=[0, 1, 0], worldUpType='vector', worldUpVector=[0, 1, 0])
            # cmds.aimConstraint(locator, postDuplicate, aimVector=[1, 0, 0], upVector=[0, 1, 0], worldUpType='vector', worldUpVector=tangentVector)
            
            cmds.parent(postDuplicate, fenceGroup)
        
            for j in range(self.numRails):
                railDuplicate = cmds.duplicate(self.railMesh, name=f'rail_{i}')[0]
                scaleFactor = self.postDistance / railSize[0]
                cmds.scale(scaleFactor, 1, 1, railDuplicate, scaleX=True)
                
                railPadding = 1 # TODO let user choose
                railDist = (postSize[2]-railPadding)/(self.numRails-1)
                
                # railX = -railPivot[0] + self.postDistance/2 + self.postDistance* i
                # railY = -railPivot[1]
                # railZ = -railPivot[2] - railDist/2 - (railDist*(self.numRails/2 -1)) + railDist * j
                
                # railX = -railPivot[0] + point[0] + postSpacing/2
                # railY = -railPivot[1] + point[1]
                
                # cmds.move(railX, railY, railZ, railDuplicate, ws=True)
                # cmds.parent(railDuplicate, fenceGroup)
            
            cmds.delete(locator)
    def getSize(self, objName):
        # Get the world bounding box of the object (min and max points in X, Y, Z)
        bbox = cmds.exactWorldBoundingBox(objName)
        
        # Calculate size in X, Y, Z directions
        sizeX = bbox[3] - bbox[0]  # maxX - minX
        sizeY = bbox[4] - bbox[1]  # maxY - minY
        sizeZ = bbox[5] - bbox[2]  # maxZ - minZ

        return (sizeX, sizeY, sizeZ)

window = FenceUI()