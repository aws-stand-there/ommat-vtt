export interface ApiListResponse {
  result: number,
  compare: string[],
  target: string[]
}

export interface ApiCrawlInfoResponse {
  timestamp: number;
  is_ongoing: boolean;
}

export interface Report {
  name: string,
  url: string,
  opeg: number,
  commits: number,
  alive_branch_count: number,
  license: string | boolean | undefined,
  languages: [
      {
          name: string,
          percent: number
      }
  ],
  alive_branches: string[],
  issue_open: string,
  issue_closed: string,
  pr_open: string,
  pr_closed: string,
  pr_approved: number,
  contributors: any,
  contributors_count: number,
  commit_graph: {
      total: number[],
      week: number[]
  }
  community_profiles: {
    README: boolean,
    CODE_OF_CONDUCT: boolean,
    LICENSE: boolean,
    CONTRIBUTING: boolean,
    ISSUE_TEMPLATE: boolean,
    PULL_REQUEST_TEMPLATE: boolean,
  },
}