#include "TriMeshPassDescription.hpp"

#include <boost/python.hpp>
#include <avango/python/register_field.h>
#include <avango/gua/renderer/TriMeshPassDescription.hpp>

using namespace boost::python;
using namespace av::python;

namespace boost
 {
  namespace python
   {
    template <class T> struct pointee<av::Link<T> >
     {
      typedef T type;
     };
   }
 }


void init_TriMeshPassDescription()
 {
  register_field<av::gua::SFTriMeshPassDescription>("SFTriMeshPassDescription");
  register_multifield<av::gua::MFTriMeshPassDescription>("MFTriMeshPassDescription");
  class_<av::gua::TriMeshPassDescription,
         av::Link<av::gua::TriMeshPassDescription>,
         bases<av::gua::PipelinePassDescription>, boost::noncopyable >("TriMeshPassDescription", "docstring", no_init)
         ;
 }
