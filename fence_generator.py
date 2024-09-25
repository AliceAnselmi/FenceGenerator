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
        self.fg.numPostsSlider = cmds.intSliderGrp(label='Number of posts:', min=2, max=100, value=0, field=True)
        self.fg.numRailsSlider = cmds.intSliderGrp(label='Rails per segment:', min=1, max=100, value=0, field=True)
        self.fg.railPaddingSlider = cmds.floatSliderGrp(label='Vertical rail padding', min=0, max=20, value=0, field=True)
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
        self.numPosts = 1
        self.numRails = 1
        self.railPadding = 0

    def generateFence(self, *args):
        if self.postMesh is None or self.railMesh is None or self.curve is None:
            cmds.warning('Please set all parameters before generating')

        cmds.select(clear = True)
        self.numPosts = int(cmds.textFieldGrp(self.numPostsSlider, query=True, text=True))
        self.numRails = int(cmds.textFieldGrp(self.numRailsSlider, query=True, text=True))
        self.railPadding = float(cmds.textFieldGrp(self.railPaddingSlider, query=True, text=True))

        # Create a group to contain the fence
        fenceGroup = cmds.group(empty=True, name='FenceGroup')

        postSize = self.getSize(self.postMesh)
        railSize = self.getSize(self.railMesh)

        cmds.select(self.postMesh, r=True)
        postPivot = cmds.getAttr('.rotatePivot')[0]
        cmds.select(self.railMesh, r=True)
        railPivot = cmds.getAttr('.rotatePivot')[0]

        minParam = cmds.getAttr(f'{self.curve}.minValue')
        maxParam = cmds.getAttr(f'{self.curve}.maxValue')

        postPositions = []

        for i in range(self.numPosts):
            postDuplicate = cmds.duplicate(self.postMesh, name=f'post_{i}')[0]

            curveParam = minParam + (i / (self.numPosts)) * (maxParam - minParam)
            point = cmds.pointOnCurve(self.curve, parameter=curveParam, position=True)
            tangent = cmds.pointOnCurve(self.curve, parameter=curveParam, tangent=True)

            # If transformations have been frozen,subtract from transform
            postX = -postPivot[0] + point[0]
            postY = -postPivot[1] + point[1]
            postZ = -postPivot[2] + point[2]
            cmds.move(postX, postY, postZ, postDuplicate)

            locator = cmds.spaceLocator(name=f'aimLocator_{i}')[0]
            locatorX = point[0] + tangent[0]
            locatorY = point[1] + tangent[1]
            locatorZ = point[2] + tangent[2]
            cmds.move(locatorX, locatorY, locatorZ, locator)
            cmds.aimConstraint(locator, postDuplicate,
                               aimVector=[1, 0, 0],
                               upVector=[0, 0, 1],
                               worldUpType='vector',
                               worldUpVector=[0, 0, 1])

            cmds.parent(postDuplicate, fenceGroup)
            postPositions.append(point)
            cmds.delete(locator)


        for i in range(self.numPosts):
            startPost = postPositions[i]
            endPost = postPositions[i + 1] if i < self.numPosts-1 else postPositions[0]
            for j in range(self.numRails):
                railDuplicate = cmds.duplicate(self.railMesh, name=f'rail_{i}_{j}')[0]
                midPoint = [
                    (startPost[0] + endPost[0]) / 2,
                    (startPost[1] + endPost[1]) / 2,
                    (startPost[2] + endPost[2]) / 2,
                ]

                # Scale the rail based on the distance between posts
                postDistance = ((endPost[0] - startPost[0]) ** 2 +
                                (endPost[1] - startPost[1]) ** 2 +
                                (endPost[2] - startPost[2]) ** 2) ** 0.5
                scaleFactor = postDistance / railSize[0]
                cmds.scale(scaleFactor, 1, 1, railDuplicate, scaleX=True)

                # Set rail position
                railDist = (postSize[2] - self.railPadding) / (self.numRails - 1)
                railX = -railPivot[0] + midPoint[0]
                railY = -railPivot[1] + midPoint[1]
                railZ = -railPivot[2] - railDist/2 - (railDist*(self.numRails/2 -1)) + railDist * j
                cmds.move(railX, railY, railZ, railDuplicate, ws=True)

                locator = cmds.spaceLocator(name=f'railLocator_{i}_{j}')[0]
                cmds.move(endPost[0], endPost[1], railZ, locator)

                # Aim the rail at the next post
                cmds.aimConstraint(locator, railDuplicate,
                                   aimVector=[1, 0, 0],
                                   upVector=[0, 0, 1],
                                   worldUpType='vector',
                                   worldUpVector=[0, 0, 1])

                cmds.parent(railDuplicate, fenceGroup)
                cmds.delete(locator)

    def getSize(self, objName):
        # Get the world bounding box of an object
        bbox = cmds.exactWorldBoundingBox(objName)

        sizeX = bbox[3] - bbox[0]
        sizeY = bbox[4] - bbox[1]
        sizeZ = bbox[5] - bbox[2]

        return (sizeX, sizeY, sizeZ)

window = FenceUI()