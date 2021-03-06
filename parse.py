#!/usr/bin/env python3

import optparse, os, re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

class AllEntities:
    def __getitem__(self, key):
        #key is your entity, you can do whatever you want with it here
        return key

def parse_network_node(node):
    try:
        ssid = node.find("ssid", recursive=False)
        gps = node.find("gps-info", recursive=False)
        if round(float(gps.find('avg-lat').string)) != 0 and round(float(gps.find('avg-lon').string)) != 0:
            return {
                'lastupdate': ssid.attrs['last-time'],
                'essid': ssid.essid.string,
                'encryption': [e.string for e in ssid.find_all('encryption', recursive=False)],
                'bssid': node.find("bssid", recursive=False).string,
                'manuf': node.find("manuf", recursive=False).string,
                'packets': int(ssid.packets.string),
                'gps': {'lat': gps.find('avg-lat').string, 'lon': gps.find('avg-lon').string}
            }
        else:
            return None

    except:
        return None

def parse_netxml(filepath):
    print("[*] Parsing {}".format(filepath))
    soup = None
    with open(filepath) as fp:
        soup = BeautifulSoup(fp, "lxml")

    networks = [parse_network_node(n) for n in soup.find_all("wireless-network", {"type": "infrastructure"})]

    return networks

    
    
def get_file_list(path):
    pattern = re.compile(".*\.netxml$")
    files = [f for f in os.listdir(path) if pattern.match(f)]
    return files

# To improve
def merge_data(data1, data2):
    data1['packets'] = data1['packets'] + data2['packets']
    
    return data1

def generate_style(soup, id, icon):
    st = soup.new_tag("Style", id=id)
    ics = soup.new_tag("IconStyle")
    ic = soup.new_tag("Icon")
    href  = soup.new_tag("href")
    href.string = icon
    ic.append(href)
    ics.append(ic)
    st.append(ics)
    return st

def generate_klm(networks, out):
    soup = BeautifulSoup(features='xml')
    kml = soup.new_tag("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = soup.new_tag("Document")

    doc.append(generate_style(soup, "standard", "http://maps.google.com/mapfiles/kml/paddle/red-stars.png"))
    doc.append(generate_style(soup, "open", "http://maps.google.com/mapfiles/kml/paddle/grn-stars.png"))
    
    for k, n in networks.items():
        if int(n["packets"]) > 0:
            pm = soup.new_tag("Placemark")
            name = soup.new_tag("name")
            name.string = "{}".format(n["essid"])        
            description = soup.new_tag("description")
            description.string = "bssid: {} \n manufactor: {} \n encryption {} \n lastupdate {} \n packets {} \n \n raw: {}".format(n["bssid"], n["manuf"], " ".join(n["encryption"]), n["lastupdate"], n["packets"], n)
            pt = soup.new_tag("Point")
            coo = soup.new_tag("coordinates")
            coo.string = "{},{}".format(n["gps"]["lon"], n["gps"]["lat"])
            
            stu = soup.new_tag("styleUrl")
            if n["encryption"] == ['None'] or n["encryption"] == []:
                stu.string="#open"
            else:
                stu.string="#standard"               
                pt.append(coo)
                pm.append(stu)            
                pm.append(name)
                pm.append(description)
                pm.append(pt)
                doc.append(pm)

    kml.append(doc)
    soup.append(kml)
    with open("{}.kml".format(out), "w") as f:        
        f.write(str(soup))


       
def main():
    parser = optparse.OptionParser('usage%prog -d <netxml directory> -o <output file>')
    parser.add_option('-d', dest='dirpath', type='string', help='specify the directory containing the netxml file')
    parser.add_option('-o', dest='output', type='string', help='specify the output file name')
    (options, args) = parser.parse_args()

    dirpath = options.dirpath
    out = options.output

    if dirpath == None or out == None:
        print(parser.usage)
        exit(0)
    
    files = get_file_list(dirpath)
    nnlist = [parse_netxml(os.path.join(dirpath, f)) for f in files]

    unique_net = {}

    for nl in nnlist:
        for n in nl:
            if n and 'bssid' in n and n['bssid']:
                if n['bssid'] not in unique_net:
                    unique_net[n['bssid']] = n
                else:
                    unique_net[n['bssid']] = merge_data(unique_net[n['bssid']], n)
                    

    generate_klm(unique_net, out)
       


if __name__ == '__main__': main()

