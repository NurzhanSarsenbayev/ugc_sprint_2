const HOST = "bench_mongo:27017";

// если уже инициализировано — ок
try {
  const s = rs.status();
  if (s && s.ok) {
    // быстрый чек: уже PRIMARY?
    try { if (db.hello().isWritablePrimary) quit(0); } catch (e) {}
  }
} catch (e) { /* not initiated yet */ }

// инициализируем, если нужно
try { rs.initiate({ _id: "rs0", members: [{ _id: 0, host: HOST }] }); } catch (e) { /* maybe already */ }

// ждём PRIMARY (макс 60 сек)
for (let i = 0; i < 60; i++) {
  try {
    if (db.hello().isWritablePrimary === true) quit(0);
  } catch (e) {}
  sleep(1000);
}
quit(1);