export type NavChild = {
  label: string;
  path: string;
};

export type NavItem = {
  label: string;
  path: string;
  icon: string;
  children?: NavChild[];
};
