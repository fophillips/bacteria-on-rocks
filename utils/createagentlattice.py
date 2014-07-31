import xml.etree.ElementTree as ET
from sys import argv
import numpy as np
import math

class CreateAgentLattice:
    def __init__(self, protocolFile, agentname, proportion):
        self.protocolFile = protocolFile
        self.agentname = agentname
        self.xmlroot = ET.parse(protocolFile).getroot()
        self.solutegrid = self.getSoluteGrid(self.xmlroot)
        self.agent = self.getAgent(self.xmlroot, self.agentname)
        self.coordinates = self.generateCoordinates(self.solutegrid,
                                                    self.agent,
                                                    proportion)
        self.density = self.parseDensity(self.xmlroot)
        self.agentstate = self.generateAgentState(self.agent,
                                                  self.coordinates,
                                                  self.density)
        self.filecontents = self.generateFileContents(self.solutegrid,
                                                      self.agent,
                                                      self.agentstate)

    @classmethod
    def getSoluteGrid(self, xmlroot):
        domainelement = xmlroot.find('world').find('computationDomain')
        gridelement = domainelement.find('grid')
        reselement = domainelement.find("param[@name='resolution']")
        grid = {
            'nDim': int(gridelement.get('nDim')),
            'nI': int(gridelement.get('nI')),
            'nJ': int(gridelement.get('nJ')),
            'nK': int(gridelement.get('nK')),
            'r': {
                'value': float(reselement.text),
                'unit': reselement.get('unit')
            }
        }
        return grid

    @classmethod
    def getAgent(cls, xmlroot, agentname):
        specieselement = xmlroot.find("species[@name='%s']" % agentname)
        r = specieselement.find("param[@name='divRadius']")
        return {
            'name': agentname,
            'radius': {
                'value': float(r.text),
                'unit': r.get('unit')
            }
        }

    @classmethod
    def generateCoordinates(cls, solutegrid, agent, proportion):
        if solutegrid['r']['unit'] != agent['radius']['unit']:
            raise Exception("Grid and agent radius units must match")
        if solutegrid['nDim'] != 2:
            raise Exception("Only 2D supported")
        res = solutegrid['r']['value']
        r = agent['radius']['value']
        xs = np.arange(r, solutegrid['nI']*res*proportion, step=r*2)
        ys = np.arange(r, solutegrid['nJ']*res, step=r*2)
        return (xs,ys)

    @classmethod
    def parseDensity(cls, xmlroot):
        density = {}
        for particle in xmlroot.findall('particle'):
            density[particle.get('name')] = float(
                particle.find("param[@name='density']").text
            )
        return density

    @classmethod
    def generateAgentState(cls, agent, coordinates, density):
        totalRadius = agent['radius']['value']
        totalMass = 4/3 * math.pi ** totalRadius**3 * density['capsule']
        family = 0
        genealogy = 0
        generation = 0
        birthday = 0
        biomass = 0
        inert = 0
        capsule = totalMass
        growthRate = 0
        volumeRate = 0
        z = 0
        r = 0
        
        state = np.empty((len(coordinates[0])*len(coordinates[1]), 14))
        i = 0
        for x in coordinates[0]:
            for y in coordinates[1]:
                state[i] = np.array((family, genealogy, generation,
                                     birthday, biomass, inert,
                                     capsule, growthRate, volumeRate,
                                     x, y, z, r, totalRadius))
                i+=1
        return state

    @classmethod
    def generateFileContents(cls, solutegrid, agent, agentstate):
        statestr = ";\n".join([','.join(["%f" % i for i in j]) for j in agentstate])
        return """
<idynomics>
  <simulation iterate="0" time="0.0" unit="hour">
    <grid resolution="%f" nI="%d" nJ="%d" nK="%d" />
    <species name="%s" header="family,genealogy,generation,birthday,biomass,inert
,capsule,growthRate,volumeRate,locationX,locationY,locationZ,radius,totalRadius">
%s;
    </species>
  </simulation>
</idynomics>""" % (solutegrid['r']['value'],
                   solutegrid['nI'],
                   solutegrid['nJ'],
                   solutegrid['nK'],
                   agent['name'],
                   statestr)

if __name__ == "__main__":
    creator = CreateAgentLattice(argv[1], argv[2], float(argv[3]))
    print(creator.filecontents)
