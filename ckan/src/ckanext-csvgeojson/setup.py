from setuptools import setup, find_packages

setup(
    name='ckanext-csvgeojson',
    version='0.1',
    description='Extension Para Diferentes Funciones',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points='''
        [ckan.plugins]  
        ckanplugin=ckanext.csvgeojson.Ckan:ckanplugin
        CsvGeoJsonApi=ckanext.csvgeojson.plugin:CSVtoGeoJSONApiPlugin
        CsvGeoJsonPlugin=ckanext.csvgeojson.CSVtoGeoJSON:CSVtoGeoJSONPlugin
        SelloExcelenciaView=ckanext.csvgeojson.sello:SelloExcelenciaView
        Odata_Api=ckanext.csvgeojson.pluginOdata:ApiODataPluginView
        ShpGeoJsonPlugin=ckanext.csvgeojson.pluginZip_Shp:ApiZipShpToGeojsonView    
        FixDateFormatPlugin=ckanext.csvgeojson.pluginFixDateFormatPlugin:FixDateFormatPlugin
        DataJSon=ckanext.csvgeojson.pluginAPI:DataJson
    ''',
)
