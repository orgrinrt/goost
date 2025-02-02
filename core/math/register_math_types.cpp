#include "register_math_types.h"

#include "geometry/register_geometry_types.h"
#include "goost/classes_enabled.gen.h"

static Ref<Random> _random;

namespace goost {

void register_math_types() {
#ifdef GOOST_Random
	_random.instance();
	ClassDB::register_class<Random>();
	Object *random = Object::cast_to<Object>(Random::get_singleton());
	Engine::get_singleton()->add_singleton(Engine::Singleton("Random", random));
#endif

#ifdef GOOST_GEOMETRY_ENABLED
	goost::register_geometry_types();
#endif
}

void unregister_math_types() {
#ifdef GOOST_Random
	_random.unref();
#endif

#ifdef GOOST_GEOMETRY_ENABLED
	goost::unregister_geometry_types();
#endif
}

} // namespace goost
