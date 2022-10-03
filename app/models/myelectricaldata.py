import json
import sys

from models.config import get_version
from models.query import Query
from models.log import log, debug


class MyElectricalData:

    def __init__(self, cache, url, usage_point_id, config):
        self.cache = cache
        self.url = url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': config['token'],
            'call-service': "myelectricaldata",
            'version': get_version()
        }

        self.usage_point_id = usage_point_id
        self.config = config
        self.contrat = {}

    def contract(self):
        name = "contracts"
        endpoint = f"{name}/{self.usage_point_id}"
        if "cache" in self.config and self.config["cache"]:
            endpoint += "/cache"
        target = f"{self.url}/{endpoint}"
        current_cache = self.cache.get_contract(usage_point_id=self.usage_point_id)
        if current_cache is None:
            # No cache
            log(f" => No cache : {target}")
            self.contrat = Query(endpoint=target, headers=self.headers).get(headers=self.headers)
            self.cache.insert_contract(usage_point_id=self.usage_point_id, contract=self.contract(), count=0)
        else:
            if "refresh_contract" in self.config and self.config["refresh_contract"] == True:
                log(f" => Refresh Cache : {target}")
                self.contrat = Query(endpoint=target, headers=self.headers).get(headers=self.headers)
                self.cache.insert_contract(usage_point_id=self.usage_point_id, contract=self.contract(), count=0)
            else:
                log(f" => Query Cache")
                contract = json.loads(query_result[1])
                query = f"INSERT OR REPLACE INTO contracts VALUES (?,?,?)"
                cur.execute(query, [pdl, json.dumps(contract), 0])
                con.commit()

        # def queryApi(url, headers, data, count=0):
        #     contract = f.apiRequest(cur, con, pdl, type="POST", url=f"{url}", headers=headers, data=json.dumps(data))
        #     if not "error_code" in contract:
        #         query = f"INSERT OR REPLACE INTO contracts VALUES (?,?,?)"
        #         cur.execute(query, [pdl, json.dumps(contract), count])
        #         con.commit()
        #     return contract
        #
        # url = main.url
        #
        # ha_discovery = {pdl: {}}
        #
        #

        # if query_result is None:
        #     f.log(" => Query API")
        #     contract = queryApi(url, headers, data)
        # else:
        #     if "refresh_contract" in pdl_config and pdl_config["refresh_contract"] == True:
        #         f.log(" => Query API (Refresh Cache)")
        #         contract = queryApi(url, headers, data, 0)
        #     else:
        #         f.log(f" => Query Cache")
        #         contract = json.loads(query_result[1])
        #         query = f"INSERT OR REPLACE INTO contracts VALUES (?,?,?)"
        #         cur.execute(query, [pdl, json.dumps(contract), 0])
        #         con.commit()
        #
        # if "error_code" in contract:
        #     f.log(contract["description"])
        #     ha_discovery = {"error_code": True, "detail": {"message": contract["description"]}}
        #     f.publish(client, f"{pdl}/contract/error", str(1))
        #     for key, value in contract.items():
        #         f.publish(client, f"{pdl}/contract/errorMsg/{key}", str(value))
        # else:
        #     f.publish(client, f"{pdl}/contract/error", str(0))
        #     if "customer" in contract:
        #         customer = contract["customer"]
        #         f.publish(client, f"{pdl}/customer_id", str(customer["customer_id"]))
        #         for usage_points in customer["usage_points"]:
        #             for usage_point_key, usage_point_data in usage_points["usage_point"].items():
        #                 f.publish(client, f"{pdl}/contract/{usage_point_key}", str(usage_point_data))
        #
        #             for contracts_key, contracts_data in usage_points["contracts"].items():
        #                 f.publish(client, f"{pdl}/contract/{contracts_key}", str(contracts_data))
        #
        #                 if contracts_key == "last_distribution_tariff_change_date":
        #                     f.publish(client, f"{pdl}/last_distribution_tariff_change_date", str(contracts_data))
        #                     ha_discovery[pdl]["last_distribution_tariff_change_date"] = str(contracts_data)
        #
        #                 if contracts_key == "last_activation_date":
        #                     f.publish(client, f"{pdl}/last_activation_date", str(contracts_data))
        #                     ha_discovery[pdl]["last_activation_date"] = str(contracts_data)
        #
        #                 if contracts_key == "subscribed_power":
        #                     f.publish(client, f"{pdl}/subscribed_power", str(contracts_data.split()[0]))
        #                     ha_discovery[pdl]["subscribed_power"] = str(contracts_data.split()[0])
        #                     config_query = f"INSERT OR REPLACE INTO config VALUES (?, ?)"
        #                     cur.execute(config_query, [f"{pdl}_subscribed_power", f"{str(contracts_data)}"])
        #                     con.commit()
        #
        #                 offpeak_hours = []
        #                 if pdl_config["offpeak_hours"] != None:
        #                     offpeak_hours = pdl_config["offpeak_hours"].split(";")
        #                 else:
        #                     if contracts_key == "offpeak_hours":
        #                         offpeak_hours = contracts_data[
        #                                         contracts_data.find("(") + 1: contracts_data.find(")")
        #                                         ].split(";")
        #
        #                 if offpeak_hours != [] and offpeak_hours != [""]:
        #                     ha_discovery[pdl]["offpeak_hours"] = offpeak_hours
        #                     index = 0
        #                     for oh in offpeak_hours:
        #                         f.publish(client, f"{pdl}/offpeak_hours/{index}/start", str(oh.split("-")[0]))
        #                         f.publish(client, f"{pdl}/offpeak_hours/{index}/stop", str(oh.split("-")[1]))
        #                         index += 1
        #                     f.publish(client, f"{pdl}/offpeak_hours", str(offpeak_hours))
        #                     offpeak_hours_store = ""
        #                     offpeak_hours_len = len(offpeak_hours)
        #                     i = 1
        #                     for hours in offpeak_hours:
        #                         offpeak_hours_store += f"{hours}"
        #                         if i < offpeak_hours_len:
        #                             offpeak_hours_store += ";"
        #                         i += 1
        #
        #                     # config_query = f"INSERT OR REPLACE INTO config VALUES (?, ?)"
        #                     # cur.execute(config_query, [f"{pdl}_offpeak_hours", f"HC ({str(offpeak_hours_store)})"])
        #                     # con.commit()
        #
        #     else:
        #         ha_discovery = {"error_code": True, "detail": {"message": contract}}
        # return ha_discovery