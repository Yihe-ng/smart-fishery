import avatar from '@/assets/images/avatar/avatar.webp'

export interface User {
  id: number
  username: string
  gender: 1 | 0
  mobile: string
  email: string
  dep: string
  status: string
  create_time: string
  avatar: string
}

// 用户列表
export const ACCOUNT_TABLE_DATA: User[] = [
  {
    id: 1,
    username: 'alexmorgan',
    gender: 1,
    mobile: '18670001591',
    email: 'alexmorgan@company.com',
    dep: '研发部',
    status: '1',
    create_time: '2020-09-09 10:01:10',
    avatar: avatar
  },
  {
    id: 2,
    username: 'sophiabaker',
    gender: 1,
    mobile: '17766664444',
    email: 'sophiabaker@company.com',
    dep: '电商部',
    status: '1',
    create_time: '2020-10-10 13:01:12',
    avatar: avatar
  },
  {
    id: 3,
    username: 'liampark',
    gender: 1,
    mobile: '18670001597',
    email: 'liampark@company.com',
    dep: '人事部',
    status: '1',
    create_time: '2020-11-14 12:01:45',
    avatar: avatar
  },
  {
    id: 4,
    username: 'oliviagrant',
    gender: 0,
    mobile: '18670001596',
    email: 'oliviagrant@company.com',
    dep: '产品部',
    status: '1',
    create_time: '2020-11-14 09:01:20',
    avatar: avatar
  },
  {
    id: 5,
    username: 'emmawilson',
    gender: 0,
    mobile: '18670001595',
    email: 'emmawilson@company.com',
    dep: '财务部',
    status: '1',
    create_time: '2020-11-13 11:01:05',
    avatar: avatar
  },
  {
    id: 6,
    username: 'noahevan',
    gender: 1,
    mobile: '18670001594',
    email: 'noahevan@company.com',
    dep: '运营部',
    status: '1',
    create_time: '2020-10-11 13:10:26',
    avatar: avatar
  },
  {
    id: 7,
    username: 'avamartin',
    gender: 1,
    mobile: '18123820191',
    email: 'avamartin@company.com',
    dep: '客服部',
    status: '2',
    create_time: '2020-05-14 12:05:10',
    avatar: avatar
  },
  {
    id: 8,
    username: 'lucasanderson',
    gender: 1,
    mobile: '18670001593',
    email: 'lucasanderson@company.com',
    dep: '市场部',
    status: '1',
    create_time: '2020-07-18 16:11:32',
    avatar: avatar
  },
  {
    id: 9,
    username: 'miawhite',
    gender: 0,
    mobile: '18670001592',
    email: 'miawhite@company.com',
    dep: '销售部',
    status: '1',
    create_time: '2020-08-01 09:12:44',
    avatar: avatar
  },
  {
    id: 10,
    username: 'williamtaylor',
    gender: 1,
    mobile: '18670001590',
    email: 'williamtaylor@company.com',
    dep: '行政部',
    status: '0',
    create_time: '2020-09-22 14:10:50',
    avatar: avatar
  }
]

export const ROLE_LIST_DATA = [
  { roleCode: 'admin', roleName: '管理员' },
  { roleCode: 'user', roleName: '普通用户' },
  { roleCode: 'editor', roleName: '编辑' }
]
