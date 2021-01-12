# Death by ACID

A tale about poorly written transactions and confusing database isolation levels.

<img src="assets/the-vat-of-acid.jpg" alt="drawing" style="width:500px;"/>
<br>

For this post to make sense, one needs to go back to 2014, where two bitcoin exchanges went bankrupt, supposedly due to use of *NoSQL* databases. The following was Flexcoin statement after the attack:    

"The attacker successfully exploited a flaw in the code which allows transfers between Flexcoin users. By sending thousands of simultaneous requests, the attacker was able to "move" coins from one user account to another until the sending account was overdrawn, before balances were updated."

So was the use of *NoSQL* really the issue and was ACID the solution 🤭?

## Synopsis

Consider a situation where a customer buys a product from a store. A customer (c) is allowed to buy any product (p) as long as c.balance (b) is >= p.price .

*Note: Products are immutable. All user attributes are immutable except for balance.*


## Implementation
This seems simple enough, right?

A typical solution in Java or Python would be something like the following:

Let's assume that you are using MySQL ([Most popular database](https://insights.stackoverflow.com/survey/2019) at the time of writing this post) for your application.

```python
# Start transaction.
with create_session() as session:
    product = session.query(Product).filter(Product._id == product_id).first()

    # Check if user has sufficient balance.
    user = session.query(User).filter(
        and_(User.pk == pk, User.balance >= product.price)
    ).first()

    if user is None:
        raise ValueError('Insufficient balance')
    
    # Update balance.
    user.balance = User.balance - product.price
# Commit.
```

Which emits the following SQL:    

```sql
-- Make sure user has sufficient balance.
SELECT users._id AS users__id, users.username AS users_username, users.balance AS users_balance 
FROM users 
WHERE users._id = %(user_id)s AND users.balance >= %(product_price)s

-- Update balance.
UPDATE users SET balance=(users.balance - %(product_price)s) WHERE users._id = %(user_id)s
```

That should be good enough, right? MySQL is an ACID-compliant database. The I in ACID stands for Isolation and MySQL provides *Repeatable Reads* by default, MySQL transactions are also [Durable](https://en.wikipedia.org/wiki/Durability_(database_systems)), [Consistant](https://en.wikipedia.org/wiki/Consistency_(database_systems)) and [Atomic](https://en.wikipedia.org/wiki/Atomicity_(database_systems)), hence ACID. A transaction is considered atomic if it's either fully applied or not applied at all with no partial or intermediate states allowed. Multiple transaction are considered isolated if their concurrent execution is equivalent to that of some sequential execution.

But, What does "Repeatable Reads (RR)" mean with respect to a transaction anyway?   

Well, It's exactly as it sounds, It's simply that If you do multiple reads within a transaction, the transction will always see the same snapshot of the concerned rows, any transaction that tries to modify the same rows will have to wait for the running transaction to finish.

Consider a situation where a user creates two simultaneous transactions (T1, T2) where he buys two separate items, The two transactions will first check if the user balance (B) cover's the item's price, To honor RR however, the two transactions can't both update user balance at the same time, since you can't have repeatable reads if the underlying values change by concurrent transactions. In other words, If T1 manages to update user's balance after T2 has started, T2 should fail to proceed as user's balance has changed since the beginning of the transaction. In a world that makes sense, that would be true, MySQL however, disagrees and will happily let T1 and T2 update B simultaneously under "RR".

## DBMS mumbo jumbo

Enter the confusing world of database isolation levels, There are four isolation levels, namely:
1. ~~Read uncommitted (Weakest)~~.
2. Read committed (Default in PostgreSQL).
3. Repeatable read (Default in MySQL).
4. ~~Serializable (Strongest)~~. 

I will refrain from discussing 1 and 4, because they are not used as the default by any popular RDBMS.

So what does "Repeatable Reads (RR)" mean after all?

Apparently it means different things to different vendors, In MySQL's case, A normal SELECT (with "RR") is not a locking READ, A "SELECT FOR UPDATE" is required for database to honor "RR". In PosgreSQL however, "RR" works as you would expect.

[**So what have Flexcoin survived the attack had they used MySQL? No, not with the default isolation level and typical ORM's implementations.**](#)
### 2. Read committed

From PostgreSQL's documentation:

"**Read Committed is the default isolation level in PostgreSQL.** When a transaction uses this isolation level, a SELECT query (without a FOR UPDATE/SHARE clause) sees only data committed before the query began; it never sees either uncommitted data or changes committed during query execution by concurrent transactions. In effect, a SELECT query sees a snapshot of the database as of the instant the query begins to run. [REDACTED]"

In Read Committed, simultaneous transactions can concurrently modify user's balance, A transaction (T1) can check user's balance while some other transaction (T2) modify it. by the time T1 tries to update the balance, It will end up updating the value commited by T2 instead of the value it observed at the begining of the transaction.

**As you can see, MySQL's RR behaves more like PostgreSQL's Read Committed.** It's true that if your criteria is simple enough, You can do match and update in a single atomic update, Which should protect against double-spending. If your update criteria is more complex however, then you are still out of luck. Neither PostgreSQL's RC or MySQL's RR will eliminate the issue, In which case you will need a more strict isolation level, like "RR" in PostgreSQL or Serializable. In a concurrent application however "Serializable" is more likely to cause deadlocks making it too costly.

[**So what have Flexcoin survived the attack had they used PostgreSQL? No, not with the default isolation level and typical ORM's implementations.**](#)

It is also worth mentioning that you could update the user's balance atomically in a NoSQL datastore, You just need to do it properly. For instance in [MongoDB](https://www.mongodb.com/) you could do the following:

```python
database.users.update_one(
        {
            '_id': _id,
            'balance': {'$gte': product.price}
        },
        {
            '$inc': {'balance': -product.price}
        }
)
```

*Note: I am not defending MongoDB here, People who have issues with MongoDB have valid points, namely [here](https://aphyr.com/posts/284-jepsen-mongodb), [here](https://aphyr.com/posts/338-jepsen-mongodb-3-4-0-rc3) and [here](https://aphyr.com/posts/322-jepsen-mongodb-stale-reads).

**So do I need ACID after all?**    

Well, A non-durable database is not a "database" and a database that is perpetually inconsistent is unreliable, But that is not what you lose when you use a NoSQL database. NoSQL databases actually offer tunable consistency (like [Cassandra](https://cassandra.apache.org/)), and while most NoSQL databases lack transactions, [**It is your fault as a developer for using them in an application where transactions are required.**](#)

ACID is not some silver bullet that will just fix poorly written software. **Even with an ACID-compliant databases and default configuration, You are still susceptible to concurrency issues similar to the one the made Flexcoin go bankrupt.**

*Some parts of the banking infrastructure are actually eventually consistent and rely on compensating actions, This is done to ensure high-availability. [[source]](http://highscalability.com/blog/2013/5/1/myth-eric-brewer-on-why-banks-are-base-not-acid-availability.html)*

## Workarounds

1. Use a stricter isolation level like Repeatable Reads, and make sure to use "SELECT FOR UPDATE" if you are usig MySQL.
2. If your filtering criteria is simple enough, then just use one atomic instruction to match and update the balance e.g. `UPDATE users SET balance = balace - price WHERE balance >= price`.
3. Few NoSQL databases actually provide tunable consistency like [Cassandra](https://cassandra.apache.org/) and [MongoDB](https://www.mongodb.com/). Recently few started supporting transactions with ACID semantics as well, like [CockroachDB](https://www.cockroachlabs.com).
 
## Tests
Tests for this post are located at [tests/](https://github.com/abdelrahman-t/death-by-acid/tree/master/src/tests).
- tests/    
    - mysql/    
    - postgresql/     
    - postgresql_rr/     
    - mongodb/    

To run tests:   
1. Install Docker and docker-compose.
2. Run `cd src && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pytest`
