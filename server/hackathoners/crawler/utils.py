from bs4 import BeautifulSoup
import os
import requests
import json
import sys
import re
import time
from pytz import timezone
from datetime import datetime
from hackathoners.config import Config
from hackathoners.db import Database

class Analyser:
    @classmethod
    def analyse(cls, repo_list):
        """
        Github를 크롤링해와서 분석합니다.
        :param repo_list 'owner/project_name' 꼴의 String List
        """
        url_array = cls.process_url(repo_list)
        processed_array = list()
        for repo, code in zip(url_array, repo_list):
            try: 
                processed_array.append(
                    cls.crawl(repo, code)
                )
            except:
                print(sys.exc_info()[0], sys.exc_info()[1])
                try: 
                    processed_array.append(
                        cls.crawl(repo, code)    
                    )
                except:
                    print(sys.exc_info()[0], sys.exc_info()[1])
                    # 두 번 실패했으므로 스킵함
                    continue

        processed_array = cls.add_del_analyze(processed_array)
        processed_array = cls.evaluate(processed_array)

        print(json.dumps(processed_array, indent=4))
        return processed_array

    @classmethod
    def crawl(cls, repo, code):
        """
        주어진 1개의 Repository에 대하여 크롤링을 시도합니다.
        :return ret 정보가 담긴 Dictionary 객체
        """
        ret = dict()
        ret["name"] = code
        ret["url"] = repo
        print("[+] Starting " + code)

        # Commits, Branch, License 고시 여부, 언어 사용 비율 추출
        print("[+] Getting fundamental information...")
        soup = BeautifulSoup(requests.get(repo).text, "html.parser")
        soup_normal_nums = soup.select("span.num.text-emphasized")
        ret["commits"] = int(soup_normal_nums[0].string.replace(",", "").strip())
        ret["alive_branch_count"] = int(soup_normal_nums[1].string.replace(",", "").strip())

        if len(soup.select(".octicon-law")) > 0:
            ret["license"] = soup.select(".octicon-law")[0].next_element.next_element.string.replace(",", "").strip()
        else:
            ret["license"] = "Unavailable"

        ret["languages"] = list()
        for lang, percent in zip(soup.select(".lang"), soup.select(".percent")):
            temp_dic = dict()
            temp_dic["name"], temp_dic["percent"] = lang.string, percent.string[0:-1]
            ret["languages"].append(temp_dic)

        ret["alive_branches"] = list()
        for branch in soup.select(".select-menu-item-text.css-truncate-target.js-select-menu-filter-text"):
            ret["alive_branches"].append(branch.string.strip())

        ret["community_profiles"] = {
            "README": False,
            "CODE_OF_CONDUCT": False,
            "LICENSE": False,
            "CONTRIBUTING": False,
            "ISSUE_TEMPLATE": False,
            "PULL_REQUEST_TEMPLATE": False,
        }

        def update_community_profile(profile_names, file_names):
            for profile_name in profile_names:
                regex = re.compile(profile_name, re.IGNORECASE)
                for file_name in file_names:
                    if regex.search(file_name.text):
                        ret["community_profiles"][profile_name] = True
                        break

        profile_names = list(ret["community_profiles"].keys())

        # README, CODE_OF_CONDUCT, LICENSE, CONTRIBUTING 확인
        file_names = soup.select(".file-wrap > table > tbody > .js-navigation-item > .content > span")
        update_community_profile(profile_names[:4], file_names)

        # ISSUE_TEMPLATE, PULL_REQUEST_TEMPLATE 확인
        default_branch_name = soup.select(".css-truncate-target[data-menu-button]")[0].text

        soup = BeautifulSoup(requests.get(repo + '/tree/' + default_branch_name + '/.github').text, "html.parser")
        file_names = soup.select(".file-wrap > table > tbody > .js-navigation-item > .content > span")
        update_community_profile(profile_names[4:], file_names)

        # 열고 닫힌 Issue의 갯수 추출
        print("[+] Getting issues...")
        soup = BeautifulSoup(requests.get(repo + "/issues").text, "html.parser")
        if len(soup.select(".states")) == 0:
            ret["issue_open"], ret["issue_closed"] = 0, 0
        else:
            issues = soup.select(".states")[0].text.strip().replace("Open", "").replace("Closed", "").replace(",", "").split()
            ret["issue_open"], ret["issue_closed"] = issues[0], issues[1]

        # 각 기여자별 Issue 갯수 추출
        # issue_url = "/" + code + "/issues?utf8=%E2%9C%93&q=is%3Aissue"
        # ret["issuers"] = dict()
        # page = 0
        # while issue_url is not None:
        #     page += 1
        #     print("[+] Issue: Page " + str(page) + " crawling...")
        #     soup = BeautifulSoup(requests.get("https://github.com" + issue_url).text, "html.parser")
        #     for i in soup.select("ul.js-active-navigation-container li"):
        #         issuer_name = i.select(".opened-by .muted-link")[0].get_text()
        #         if issuer_name in ret["issuers"]:
        #             ret["issuers"][issuer_name] += 1
        #         else:
        #             ret["issuers"][issuer_name] = 1

        #     next_page = soup.select(".next_page")
        #     if len(next_page) == 0:
        #         break
            
        #     issue_url = next_page[0].get("href")

        # 열고 닫힌 Pull Requests의 갯수 추출
        print("[+] Getting pull requests...")
        soup = BeautifulSoup(requests.get(repo + "/pulls").text, "html.parser")
        if len(soup.select(".states")) == 0:
            ret["pr_open"], ret["pr_closed"] = 0, 0
        else:
            pulls = soup.select(".states")[0].text.strip().replace("Open", "").replace("Closed", "").replace(",", "").split()
            ret["pr_open"], ret["pr_closed"] = pulls[0], pulls[1]

        # 기여자 추출
        print("[+] Getting contributors...")
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Referrer": "https://github.com/" + code + "/graphs/commit-activity"
        }

        ret["contributors"] = dict()
        ret["contributors_count"] = 0

        commit_url = "https://github.com/" + code + "/commits/master"
        page = 0

        while commit_url is not None:
            page += 1
            print("[+] Commits: Page " + str(page))
            soup = BeautifulSoup(requests.get(commit_url, headers=headers).text, "html.parser")
            for i in soup.select(".commit-author"):
                author = i.text.strip()
                if author in ret["contributors"]:
                    ret["contributors"][author] += 1
                else:
                    ret["contributors"][author] = 1
                    ret["contributors_count"] += 1

            next_link = soup.select(".pagination > a")
            if len(next_link) != 0 and next_link[0].text.strip() == "Older":
                commit_url = next_link[0]["href"]
            else:
                commit_url = None

        # Pulse
        print("[+] Getting Pulse data...")
        commit_graph_url = "https://github.com/" + code + "/graphs/commit-activity-data"
        res = requests.get(commit_graph_url, headers=headers).json()
        total, week = list(), list()
        for i in range(52):
            total.append(res[i]['total'])
            week.append(res[i]['week'])
        ret["commit_graph"] = {
            "total": total, "week": week
        }
        
        # Github의 Abuse Detection을 회피하기 위한 3초 Sleep
        print("[+] Avoiding GitHub abuse detection...")
        time.sleep(3)
        return ret

    @classmethod
    def add_del_analyze(cls, report_list):
        """
        주어진 팀 정보에 대해 addition, deletion 수치를 측정합니다.
        """

        print("[+] Start Add/Del Analyzer")

        t = time.time()

        home = os.getcwd()

        if not os.path.exists("./temp"):
            os.mkdir("./temp")

        for report in report_list:
            repo_url = report["url"]
            repo_name = report["name"]

            before_scripts = [
                "git clone {} ./temp/{} > ./temp/temp.txt".format("{}.git".format(repo_url), repo_name),
                "cd ./temp/{}".format(repo_name),
                "git --no-pager log --shortstat | grep 'files changed' > ./log.txt",
            ]
            os.system("; ".join(before_scripts))

            os.system("pwd")

            fileobj = open("./temp/{}/log.txt".format(repo_name), 'r')

            commits = list()
            while True:
                line = fileobj.readline()
                if not line: break

                temp = line.split(",")

                commit = dict()
                for i in temp:
                    if "changed" in i:
                        commit["changed"] = int(i.replace(" files changed", "").replace(" ", "").replace("\n", ""))
                    elif "insertions" in i:
                        commit["add"] = int(i.replace(" insertions(+)", "").replace(" ", "").replace("\n", ""))
                    elif "deletions" in i:
                        commit["del"] = int(i.replace(" deletions(-)", "").replace(" ", "").replace("\n", ""))

                if "add" not in commit:
                    commit["add"] = 0
                if "del" not in commit:
                    commit["del"] = 0

                commits.append(commit)

            fileobj.close()

            result = {"changed" : 0, "add" : 0, "del" : 0}
            for commit in commits:
                for key, value in commit.items():
                    if key == "changed":
                        result[key] += value < 30
                    elif key == "add":
                        result[key] += value < 10000
                    elif key == "del":
                        result[key] += value < 10000

            score = result["add"] / len(commits) * 0.35 \
                                       + result["del"] / len(commits) * 0.35 \
                                       + result["changed"] / len(commits) * 0.3
            report["per_valid_commit"] = round(score, 3)

        os.system("rm -rf ./temp")

        print("{}s".format(time.time() - t))
        return report_list

    @classmethod
    def evaluate(cls, report_list):
        """
        주어진 팀 정보와 해석된 Repo 정보를 바탕으로 OPEG 점수를 계산합니다.
        @return report_list 각 팀의 점수가 담긴 Dictionary 리스트
        """
        for report in report_list:
            opeg_score = report["commits"] * 10 * report["per_valid_commit"] \
                        + (int(report["issue_open"]) + int(report["issue_closed"])) * 1 \
                        + (1 if report["license"] != "" else 0) * 1 \
                        + (int(report["pr_open"]) + int(report["pr_closed"])) * 1 \
                        + report["contributors_count"] * 1 \
                        + report["alive_branch_count"] * 1 \
                        + sum(report["community_profiles"].values()) * 3
            report["opeg"] = round(opeg_score, 3)

        return report_list

    @classmethod
    def process_url(cls, repo_list):
        """
        주어진 Repo 정보를 바탕으로 URL을 만듭니다.
        @return url_array 인식된 전체 Repo의 URL 리스트
        """
        url_array = list()
        github_prefix = "https://github.com/"

        for repo in repo_list:
            if repo.count("/") != 1:
                # Repository의 표현식에 오류가 있는 경우
                # 사전에 UI 단 입력에서 걸러줘야 하므로 여기서는 무시함
                continue
            url_array.append(github_prefix + repo)

        return url_array