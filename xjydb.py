from neo4j import GraphDatabase
from datetime import datetime
import pytz

class Neo4jHandler:
    def __init__(self, uri, user, password, label="Danmu"):
        # 连接数据库
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 1. 词云展示用的标签 (例如: Danmu_xujiying)
        self.cloud_label = label 
        
        # 2. 后台记录用的标签 (自动生成, 例如: Log_xujiying)
        suffix = label.split("_")[-1] if "_" in label else label
        self.log_label = f"Log_{suffix}"

    def close(self):
        self.driver.close()

    def add_record(self, student_name, content):
        """同时记录词云统计和学生日志"""
        with self.driver.session() as session:
            # 获取北京时间
            tz = pytz.timezone('Asia/Shanghai')
            current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

            query = f"""
            // 1. 维护词云统计 (如果有则累加，没有则创建)
            MERGE (c:{self.cloud_label} {{name: $content}})
            ON CREATE SET c.value = 1
            ON MATCH SET c.value = c.value + 1
            
            // 2. 插入一条流水日志 (记录是谁、什么时间发的)
            CREATE (l:{self.log_label} {{
                student_name: $student_name,
                content: $content,
                create_time: $current_time
            }})
            """
            session.run(query, student_name=student_name, content=content, current_time=current_time)

    def get_cloud_data(self):
        """获取词云展示数据"""
        with self.driver.session() as session:
            query = f"""
            MATCH (n:{self.cloud_label})
            RETURN n.name as name, n.value as value
            ORDER BY n.value DESC
            LIMIT 100
            """
            result = session.run(query)
            return [{"name": r["name"], "value": r["value"]} for r in result]

    def get_logs(self):
        """获取后台管理日志"""
        with self.driver.session() as session:
            query = f"""
            MATCH (l:{self.log_label})
            RETURN l.student_name as name, l.content as content, l.create_time as time
            ORDER BY l.create_time DESC
            """
            result = session.run(query)
            return [{"时间": r["time"], "姓名": r["name"], "内容": r["content"]} for r in result]

    def clear_cloud_only(self):
        """只清空词云展示数据，保留后台日志"""
        with self.driver.session() as session:
            query = f"""
            MATCH (n:{self.cloud_label})
            DETACH DELETE n
            """
            session.run(query)
    
    def clear_all(self):
        """清空当前标签下的所有数据（包括词云和日志）"""
        with self.driver.session() as session:
            query = f"""
            MATCH (n) 
            WHERE n:{self.cloud_label} OR n:{self.log_label}
            DETACH DELETE n
            """
            session.run(query)