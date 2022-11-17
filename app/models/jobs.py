import __main__ as app
import sys
import traceback

from models.config import get_version
from models.database import Database
from models.export_mqtt import ExportMqtt
from models.export_home_assistant import HomeAssistant
from models.export_influxdb import ExportInfluxDB
from models.log import Log
from models.query_address import Address
from models.query_contract import Contract
from models.query_daily import Daily
from models.query_detail import Detail
from models.query_status import Status

DB = Database()
LOG = Log()


class Job:
    def __init__(self, usage_point_id=None):
        self.config = app.CONFIG
        self.usage_point_id = usage_point_id
        self.usage_point_config = {}
        self.mqtt_config = self.config.mqtt_config()
        self.home_assistant_config = self.config.home_assistant_config()
        self.influxdb_config = self.config.influxdb_config()

    def job_import_data(self, target=None):
        if app.DB.lock_status():
            return {
                "status": False,
                "notif": "Importation déjà en cours..."
            }
        else:
            DB.lock()
            if self.usage_point_id is None:
                self.usage_points = DB.get_usage_point_all()
            else:
                self.usage_points = [DB.get_usage_point(self.usage_point_id)]
            for self.usage_point_config in self.usage_points:
                self.usage_point_id = self.usage_point_config.usage_point_id
                LOG.log_usage_point_id(self.usage_point_id)
                try:
                    if target == "gateway_status" or target is None:
                        self.get_gateway_status()
                    if target == "account_status" or target is None:
                        self.get_account_status()
                    if target == "contract" or target is None:
                        self.get_contract()
                    if target == "addresses" or target is None:
                        self.get_addresses()
                    if target == "consumption" or target is None:
                        self.get_consumption()
                    if target == "consumption_detail" or target is None:
                        self.get_consumption_detail()
                    if target == "production" or target is None:
                        self.get_production()
                    if target == "production_detail" or target is None:
                        self.get_production_detail()
                except Exception as e:
                    LOG.error(e)
                    LOG.error([
                        f"Erreur lors de la récupération des données du point de livraison {self.usage_point_config.usage_point_id}",
                        f"Un nouvel essaie aura lien dans {app.CYCLE}s"
                    ])

                try:
                    # #######################################################################################################
                    # # MQTT
                    if "enable" in self.mqtt_config and self.mqtt_config["enable"]:
                        if target == "mqtt" or target is None:
                            self.mqtt_contract()
                            self.mqtt_address()
                            if hasattr(self.usage_point_config, "consumption") and self.usage_point_config.consumption:
                                ExportMqtt(self.usage_point_id, "consumption").daily_annual(
                                    self.usage_point_config.consumption_price_base
                                )
                                ExportMqtt(self.usage_point_id, "consumption").daily_linear(
                                    self.usage_point_config.consumption_price_base
                                )
                            if hasattr(self.usage_point_config, "production") and self.usage_point_config.production:
                                ExportMqtt(self.usage_point_id, "production").daily_annual(
                                    self.usage_point_config.production_price
                                )
                                ExportMqtt(self.usage_point_id, "production").daily_linear(
                                    self.usage_point_config.production_price
                                )
                            if hasattr(self.usage_point_config,
                                       "consumption_detail") and self.usage_point_config.consumption_detail:
                                ExportMqtt(self.usage_point_id, "consumption").detail_annual(
                                    self.usage_point_config.consumption_price_hp,
                                    self.usage_point_config.consumption_price_hc
                                )
                                ExportMqtt(self.usage_point_id, "consumption").detail_linear(
                                    self.usage_point_config.consumption_price_hp,
                                    self.usage_point_config.consumption_price_hc
                                )
                            if hasattr(self.usage_point_config,
                                       "production_detail") and self.usage_point_config.production_detail:
                                ExportMqtt("production").detail_annual(self.usage_point_config.production_price)
                                ExportMqtt("production").detail_linear(self.usage_point_config.production_price)
                    #######################################################################################################
                    # HOME ASSISTANT
                    if "enable" in self.home_assistant_config and self.home_assistant_config["enable"]:
                        if "enable" in self.mqtt_config and self.mqtt_config["enable"]:
                            if target == "home_assistant" or target is None:
                                HomeAssistant(self.usage_point_id).export(
                                    self.usage_point_config.consumption_price_base,
                                    self.usage_point_config.consumption_price_hp,
                                    self.usage_point_config.consumption_price_hc
                                )
                        else:
                            app.LOG.critical("L'export Home Assistant est dépendant de MQTT, "
                                             "merci de configurer MQTT avant d'exporter vos données dans Home Assistant")
                    #######################################################################################################
                    # INFLUXDB
                    if "enable" in self.influxdb_config and self.influxdb_config["enable"]:
                        # app.INFLUXDB.purge_influxdb()
                        if target == "influxdb" or target is None:
                            if hasattr(self.usage_point_config, "consumption") and self.usage_point_config.consumption:
                                ExportInfluxDB(self.usage_point_id).daily(
                                    self.usage_point_config.consumption_price_base,
                                )
                            if hasattr(self.usage_point_config, "production") and self.usage_point_config.production:
                                ExportInfluxDB(self.usage_point_id).daily(
                                    self.usage_point_config.production_price,
                                    "production"
                                )
                            if hasattr(self.usage_point_config, "consumption_detail") and self.usage_point_config.consumption_detail:
                                ExportInfluxDB(self.usage_point_id).detail(
                                    self.usage_point_config.consumption_price_hp,
                                    self.usage_point_config.consumption_price_hc
                                )
                            if hasattr(self.usage_point_config, "production_detail") and self.usage_point_config.production_detail:
                                ExportInfluxDB(self.usage_point_id).detail(
                                    self.usage_point_config.production_price,
                                    "production_detail"
                                )
                except Exception as e:
                    traceback.print_exc()
                    LOG.error(e)
                    LOG.error([
                        f"Erreur lors de l'exportation des données du point de livraison {self.usage_point_config.usage_point_id}",
                        f"Un nouvel essaie aura lien dans {app.CYCLE}s"
                    ])
            LOG.finish()
            DB.unlock()
            return {
                "status": True,
                "notif": "Importation terminée"
            }

    def header_generate(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': self.usage_point_config.token,
            'call-service': "myelectricaldata",
            'version': get_version()
        }

    def get_gateway_status(self):
        LOG.title(f"[{self.usage_point_config.usage_point_id}] Status de la passerelle :")
        result = Status(
            headers=self.header_generate(),
        ).ping()
        return result

    def get_account_status(self):
        LOG.title(f"[{self.usage_point_config.usage_point_id}] Check account status :")
        result = Status(
            headers=self.header_generate(),
        ).status(usage_point_id=self.usage_point_config.usage_point_id)
        return result

    def get_contract(self):
        LOG.title(f"[{self.usage_point_config.usage_point_id}] Récupération du contrat :")
        result = Contract(
            headers=self.header_generate(),
            usage_point_id=self.usage_point_config.usage_point_id,
            config=self.usage_point_config
        ).get()
        if "error" in result and result["error"]:
            LOG.error(result["description"])
        return result

    def get_addresses(self):
        LOG.title(f"[{self.usage_point_config.usage_point_id}] Récupération de coordonnée :")
        result = Address(
            headers=self.header_generate(),
            usage_point_id=self.usage_point_config.usage_point_id,
            config=self.usage_point_config
        ).get()
        if "error" in result and result["error"]:
            LOG.error(result["description"])
        return result

    def get_consumption(self):
        result = {}
        if hasattr(self.usage_point_config, "consumption") and self.usage_point_config.consumption:
            LOG.title(f"[{self.usage_point_config.usage_point_id}] Récupération de la consommation journalière :")
            result = Daily(
                headers=self.header_generate(),
                usage_point_id=self.usage_point_config.usage_point_id,
                config=self.usage_point_config,
            ).get()
        return result

    def get_consumption_detail(self):
        result = {}
        if hasattr(self.usage_point_config, "consumption_detail") and self.usage_point_config.consumption_detail:
            LOG.title(f"[{self.usage_point_config.usage_point_id}] Récupération de la consommation détaillé :")
            result = Detail(
                headers=self.header_generate(),
                usage_point_id=self.usage_point_config.usage_point_id,
                config=self.usage_point_config,
            ).get()
        return result

    def get_production(self):
        result = {}
        if hasattr(self.usage_point_config, "production") and self.usage_point_config.production:
            LOG.title(f"[{self.usage_point_config.usage_point_id}] Récupération de la production journalière :")
            result = Daily(
                headers=self.header_generate(),
                usage_point_id=self.usage_point_config.usage_point_id,
                config=self.usage_point_config,
                measure_type="production"
            ).get()
        return result

    def get_production_detail(self):
        result = {}
        if hasattr(self.usage_point_config, "production_detail") and self.usage_point_config.production_detail:
            LOG.title(f"[{self.usage_point_config.usage_point_id}] Récupération de la production détaillé :")
            result = Detail(
                headers=self.header_generate(),
                usage_point_id=self.usage_point_config.usage_point_id,
                config=self.usage_point_config,
                measure_type="production"
            ).get()
        return result

    def mqtt_contract(self):
        LOG.title(f"[{self.usage_point_config.usage_point_id}] Exportation de données dans MQTT.")

        LOG.log("Génération des messages du contrat")
        contract_data = app.DB.get_contract(self.usage_point_id)
        if hasattr(contract_data, "__table__"):
            output = {}
            for column in contract_data.__table__.columns:
                output[f"{self.usage_point_id}/contract/{column.name}"] = str(getattr(contract_data, column.name))
            app.MQTT.publish_multiple(output)
            LOG.log(" => Finish")
        else:
            LOG.log(" => Failed")

    def mqtt_address(self):
        LOG.log("Génération des messages d'addresse")
        address_data = app.DB.get_addresse(self.usage_point_id)
        if hasattr(address_data, "__table__"):
            output = {}
            for column in address_data.__table__.columns:
                output[f"{self.usage_point_id}/address/{column.name}"] = str(getattr(address_data, column.name))
            app.MQTT.publish_multiple(output)
            LOG.log(" => Finish")
        else:
            LOG.log(" => Failed")

    def home_assistant(self):
        if "enable" in self.home_assistant_config and self.home_assistant_config["enable"]:
            LOG.title(
                f"[{self.usage_point_config.usage_point_id}] Exportation de données dans Home Assistant (via l'auto-discovery MQTT).")
            daily = app.DB.get_daily_all(self.usage_point_id, "consumption")
        return daily

    def influxdb(self):
        result = {}
        if "enable" in self.influxdb_config and self.influxdb_config["enable"]:
            LOG.title(f"[{self.usage_point_config.usage_point_id}] Exportation de données dans InfluxDB.")
        return result