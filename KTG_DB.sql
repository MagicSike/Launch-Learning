DROP TABLE IF EXISTS USERS;
DROP TABLE IF EXISTS PRODUCTS;
DROP TABLE IF EXISTS POSTS;
DROP TABLE IF EXISTS INTERACTS;
DROP TABLE IF EXISTS COMMENTS;
DROP TABLE IF EXISTS REPLY;
DROP TABLE IF EXISTS FORGOT;
DROP TABLE IF EXISTS BUILDS;
DROP TABLE IF EXISTS LIKE_DISLIKE;

CREATE TABLE USERS (
  users_id INTEGER NOT NULL,  -- when row is inserted, user_id is set to 1,2,3..., onwards...
  users_name VARCHAR(40) NOT NULL,				-- ... INSERT INTO USERS VALUES('Kevin', '123456789', 'a@gmail.com'), no need to manually set user_id
  user_password VARCHAR(250) NOT NULL, --should be hashed later on
  user_email VARCHAR(40) NOT NULL,
  user_session DATE DEFAULT NULL,
  profile_pic_name VARCHAR(40) DEFAULT NULL,	

  profile_description VARCHAR(250) DEFAULT NULL,

  PRIMARY KEY (users_id),
  UNIQUE (users_name, user_email, user_password)
);

CREATE TABLE FORGOT (
  u_id INTEGER NOT NULL,
  forgot_code INTEGER NOT NULL, 
  code_timer DATE NOT NULL,
  
  PRIMARY KEY (u_id, forgot_code)
  FOREIGN KEY (u_id) REFERENCES USERS(users_id) ON DELETE CASCADE
);

CREATE TABLE PRODUCTS (
  product_id INTEGER NOT NULL, --id starts at 10,000
  product_name VARCHAR(250) NOT NULL, 
  product_link VARCHAR(250) NOT NULL,
  product_image VARCHAR(250) NOT NULL,
  product_type VARCHAR(50) NOT NULL,
  product_price DECIMAL(6,2) DEFAULT 0,
  product_color INTEGER DEFAULT 0,
  product_profile VARCHAR(100) DEFAULT NULL,
  product_top INTEGER DEFAULT 0,
  product_sizing VARCHAR(25) DEFAULT NULL,
  product_brand VARCHAR(25) DEFAULT NULL,
  product_material VARCHAR(25) DEFAULT NULL,
  product_switch_type VARCHAR(25) DEFAULT NULL,
  product_mount VARCHAR(25) DEFAULT NULL,
  product_hsf VARCHAR(25) DEFAULT NULL,

  PRIMARY KEY (product_id),
  UNIQUE (product_name)
);

CREATE TABLE POSTS (
  post_id INTEGER NOT NULL, --post id starts at 20,000
  u_id INTEGER NOT NULL,
  p_title VARCHAR(50) DEFAULT NULL,
  p_text VARCHAR(500) NOT NULL,
  type_of_text VARCHAR(20) NOT NULL,
  p_post_date DATETIME,

  PRIMARY KEY (post_id),
  FOREIGN KEY (u_id) REFERENCES USERS(users_id) ON DELETE CASCADE
);

CREATE TABLE LIKE_DISLIKE (
  community_post_id INTEGER NOT NULL, 
  interact_user_id INTEGER NOT NULL,
  like_dislike INTEGER DEFAULT 0, -- 1 is like / 2 is dislike

  PRIMARY KEY (community_post_id, interact_user_id),
  FOREIGN KEY (community_post_id) REFERENCES POSTS(post_id) ON DELETE CASCADE
  FOREIGN KEY (interact_user_id) REFERENCES USERS(interact_user_id) ON DELETE CASCADE
);

CREATE TABLE COMMENTS (
  pro_id INTEGER NOT NULL,
  p_id INTEGER NOT NULL,

  PRIMARY KEY (pro_id, p_id),
  FOREIGN KEY (pro_id) REFERENCES PRODUCTS(product_id) ON DELETE CASCADE,
  FOREIGN KEY (p_id) REFERENCES POSTS(post_id) ON DELETE CASCADE
);

CREATE TABLE REPLY (
  community_post_id INTEGER NOT NULL, 
  reply_post_id INTEGER NOT NULL,

  PRIMARY KEY (community_post_id, reply_post_id),
  FOREIGN KEY (community_post_id) REFERENCES POSTS(post_id) ON DELETE CASCADE
  FOREIGN KEY (reply_post_id) REFERENCES POSTS(post_id) ON DELETE CASCADE
);

CREATE TABLE BUILDS (
  build_id INTEGER NOT NULL, -- build_id start 1 
  build_user_id INTEGER NOT NULL, 
  cases_id INTEGER DEFAULT NULL, 
  pcb_id INTEGER DEFAULT NULL, 
  plates_id INTEGER DEFAULT NULL, 
  switches_id INTEGER DEFAULT NULL, 
  keycaps_id INTEGER DEFAULT NULL, 
  removed_status INTEGER NOT NULL DEFAULT 0, 

  PRIMARY KEY (build_id),
  FOREIGN KEY (build_user_id) REFERENCES USERS(users_id) ON DELETE CASCADE
  FOREIGN KEY (cases_id) REFERENCES USERS(product_id) ON DELETE SET NULL
  FOREIGN KEY (pcb_id) REFERENCES USERS(product_id) ON DELETE SET NULL
  FOREIGN KEY (plates_id) REFERENCES USERS(product_id) ON DELETE SET NULL
  FOREIGN KEY (switches_id) REFERENCES USERS(product_id) ON DELETE SET NULL
  FOREIGN KEY (keycaps_id) REFERENCES USERS(product_id) ON DELETE SET NULL
);