import Axios, { AxiosInstance } from 'axios';
import * as React from 'react';
import { Bar, Doughnut } from 'react-chartjs-2';
import { Report } from 'src/types';

import * as constants from '../../constants';
import './report.css';

interface ReportPageState {
  load: boolean,
  report?: Report,
  timestamp?: number,
  is_ongoing?: boolean
}

export class ReportPage extends React.Component<any, ReportPageState> {
  public state: ReportPageState = {
    load: false,
    report: undefined
  };

  private axios: AxiosInstance = Axios.create({
    baseURL: constants.API_SERVER_URL
  });
  
  public componentDidMount = () => {
    const {owner, project} = this.props.match.params;
    this.axios.post("/api/detail", {repo: owner + "/" + project})
      .then((resp) => {
        const data: any = resp.data;
        if (data.result === 1) {
          this.setState({
            load: true,
            report: undefined,
            timestamp: undefined,
            is_ongoing: undefined
          });
        } else {
          this.setState({
            load: true,
            report: data.detail,
            timestamp: data.timestamp,
            is_ongoing: data.is_ongoing
          });
        }
      })
      .catch((err) => {
        alert("서버와의 통신 중 오류가 발생했습니다. 나중에 다시 시도하세요.")
      });
  }

  public renderLoad = () => (
    <div>
      불러오는 중...
    </div>
  );
  
  public decideColor = (data: number[]) => {
    const sum = data.reduce((p, c) => p + c, 0);
    const result: string[] = [];
    data.forEach(v => {
      const percent = v / sum;
      result.push(`rgba(20, 29, 37, ${percent + 0.1}`);
    });
    return result;
  }
  
  public render() {
    if (!this.state.load) {
      return this.renderLoad();
    }
    if (this.state.report === undefined) {
      alert("서버에 보고서가 존재하지 않습니다.\nCrawling을 재요청해주세요.");
      location.href = "/";
      return;
    }

    // Fundamentals
    const report: Report = this.state.report;
    const timestamp: Date = new Date(this.state.timestamp! * 1000);

    // Date string by locale
    const reportDate: string = (this.state.is_ongoing!) ? "현재 Crawling 중입니다. 잠시 후 새로고침하세요." : timestamp.toLocaleDateString() + " " + timestamp.toLocaleTimeString();

    // Community profiles
    const totalCommunityProfiles = Object.keys(report.community_profiles).length;
    const checkedCommunityProfiles = Object.keys(report.community_profiles).filter(
      profileName => report.community_profiles[profileName] === true
    ).length;

    // Language string
    const languages = report.languages.map(v => {
      const {name, percent} = v;
      return  name + " (" + percent + "%)";
    }).join(", ");

    // Contributor metrics
    const contributorLabel = Object.keys(report.contributors).sort(
      (keyA: string, keyB: string) => report.contributors[keyB] - report.contributors[keyA]
    ).slice(0, 30);
    const contributorValue: number[] = contributorLabel.map(v => {
      return report.contributors[v];
    });

    // Commit metrics
    const commitTotal: number[] = report.commit_graph.total;
    const commitLabel: string[] = report.commit_graph.week.map(v => {
      const realDate = new Date(v * 1000);
      return (realDate.getMonth() + 1).toString() + "/" + (realDate.getDate().toString());
    });

    // Find index for cutting zero data
    let cuttingIndex = 0;
    for (let i = 0; i < commitTotal.length; i++) {
      if (commitTotal[i] > 0) {
        cuttingIndex = i;
        break
      }
    }
    commitTotal.splice(0, cuttingIndex);
    commitLabel.splice(0, cuttingIndex);

    const commitStartDateText = commitLabel[0];
    const commitEndDateText = commitLabel[commitLabel.length - 1];


    return (
      <div className="container report__wrapper">
        <h1>분석 보고서: <span className="text-gray">{report.name}</span></h1>
        <hr/>
        <div className="block-container">
          <h3 className="block-title">기본 정보</h3>
          <table className="table table-bordered table-striped">
            <tbody>
              <tr>
                <th scope="row">이름</th>
                <td>{report.name}</td>
              </tr>
              <tr>
                <th scope="row">Repository 주소</th>
                <td><a href={"https://github.com/" + report.name}>https://github.com/{report.name}</a></td>
              </tr>
              <tr>
                <th scope="row">소유자 Profile 주소</th>
                <td><a href={"https://github.com/" + report.name.split("/")[0]}>https://github.com/{report.name.split("/")[0]}</a></td>
              </tr>
              <tr>
                <th scope="row">검사 기준 시간</th>
                <td>{reportDate}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="block-container">
          <h3 className="block-title">Repository 정보</h3>
          <table className="table table-bordered table-striped">
            <tbody>
              <tr>
                <th scope="row">License</th>
                <td>{report.license}</td>
              </tr>
              <tr>
                <th scope="row">Languages</th>
                <td>{languages}</td>
              </tr>
              <tr>
                <th scope="row">Commit <span className="badge badge-primary">참여 지표</span></th>
                <td>총 <strong>{report.commits.toLocaleString()}개</strong></td>
              </tr>
              <tr>
                <th scope="row">Vaild Commit <span className="badge badge-primary">참여 지표</span></th>
                <td><strong>{report.per_valid_commit}%</strong></td>
              </tr>
              <tr>
                <th scope="row">Contributor <span className="badge badge-primary">참여 지표</span></th>
                <td>총 <strong>{report.contributors_count.toLocaleString()}명</strong>의 Official Contributor</td>
              </tr>
              <tr>
                <th scope="row">Issue <span className="badge badge-primary">참여 지표</span></th>
                <td>총 <strong>{(parseInt(report.issue_open, 10) + parseInt(report.issue_closed, 10)).toLocaleString()}개</strong>: {parseInt(report.issue_open, 10).toLocaleString()}개 열림, {parseInt(report.issue_closed, 10).toLocaleString()}개 닫힘</td>
              </tr>
              <tr>
                <th scope="row">Pull Request <span className="badge badge-primary">참여 지표</span></th>
                <td>총 <strong>{(parseInt(report.pr_open, 10) + parseInt(report.pr_closed, 10)).toLocaleString()}개</strong>: {parseInt(report.pr_open, 10).toLocaleString()}개 열림, {parseInt(report.pr_closed, 10).toLocaleString()}개 닫힘</td>
              </tr>
              <tr>
                <th scope="row">Pull Request (Approved) <span className="badge badge-primary">참여 지표</span></th>
                <td>총 <strong>{report.pr_approved}개</strong></td>
              </tr>
              <tr>
                <th scope="row">Community Profile <span className="badge badge-primary">참여 지표</span></th>
                <td>총 {totalCommunityProfiles}개 중 <strong>{checkedCommunityProfiles}개</strong> 기재됨</td>
              </tr>
              <tr>
                <th scope="row">OPEG 점수</th>
                <td><strong>{report.opeg.toLocaleString()}점</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="block-container">
          <h3 className="block-title">Community Profile 정보</h3>
          <table className="table table-bordered table-striped">
            <tbody>
              <tr>
                <th scope="row" style={{ width: '30%' }}>README</th>
                <td className="col-9">{report.community_profiles.README ? '기재됨': '없음'}</td>
              </tr>
              <tr>
                <th scope="row">CODE_OF_CONDUCT</th>
                <td>{report.community_profiles.CODE_OF_CONDUCT ? '기재됨': '없음'}</td>
              </tr>
              <tr>
                <th scope="row">LICENSE</th>
                <td>{report.community_profiles.LICENSE ? '기재됨': '없음'}</td>
              </tr>
              <tr>
                <th scope="row">CONTRIBUTING</th>
                <td>{report.community_profiles.CONTRIBUTING ? '기재됨': '없음'}</td>
              </tr>
              <tr>
                <th scope="row">ISSUE_TEMPLATE</th>
                <td>{report.community_profiles.ISSUE_TEMPLATE ? '기재됨': '없음'}</td>
              </tr>
              <tr>
                <th scope="row">PULL_REQUEST_TEMPLATE</th>
                <td>{report.community_profiles.PULL_REQUEST_TEMPLATE ? '기재됨': '없음'}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div className="block-container">
          <h3 className="block-title">전체 참여율 분포 (Top 50)</h3>
          <Doughnut
            data={{
              labels: contributorLabel,
              datasets: [{
                label: "Contribution (Commits)",
                data: contributorValue,
                backgroundColor: this.decideColor(contributorValue)
              }]
            }}/>
        </div>
        <div className="block-container">
          <h3 className="block-title">주 단위 Commit 분포 ({`${commitStartDateText}~${commitEndDateText}`})</h3>
          <Bar
            data={{
              labels: commitLabel,
              datasets: [{
                label: "Commits of the week",
                data: commitTotal,
                backgroundColor: '#34495e',
                borderColor: '#2c3e50',
                borderWidth: 1
              }]
            }}/>
        </div>
      </div>
    )
  }
}
